from discord import Embed, Role, utils
from discord.ext import commands
from .utils import checks
import itertools
import operator


class ReactRoles:
	"""Use message reactions to manage selfroles"""

	def __init__(self, bot):
		self.bot = bot
		if "Role Management" not in self.bot.categories:
			self.bot.categories["Role Management"] = [type(self).__name__]
		elif type(self).__name__ not in self.bot.categories["Role Management"]:
			self.bot.categories["Role Management"].append(type(self).__name__)

	@commands.command()
	@checks.is_admin()
	async def rolewizard(self, ctx):
		"""A wizard to guide you through the process of setting up self assignable roles"""

		embed = Embed(title=f"React Roles for {ctx.guild.name}",
		              description="Enter the #channel for the react roles to take place")
		original_message = await ctx.send(embed=embed)

		def message_channel_author_check(check_message):
			return (check_message.channel is ctx.channel) and (check_message.author is ctx.author)

		def react_channel_author_check(check_reaction, check_user):
			return (check_reaction.message.channel is ctx.channel) and (check_user is ctx.author)

		channel = None

		while not channel:
			message = await self.bot.wait_for("message", check=message_channel_author_check, timeout=120.0)

			if not message.channel_mentions:
				embed.description = "Invalid Channel. Please enter a valid channel"
				await message.delete()
				await original_message.edit(embed=embed)
			else:
				channel = message.channel_mentions[0]
				await message.delete()

		embed.add_field(name="Channel", value=f"{channel.mention}")

		embed.description = "Channel accepted, Please mention role you wish to add"
		await original_message.edit(embed=embed)

		ended = False
		roles = []
		while not ended:
			role = None
			while not role:
				message = await self.bot.wait_for("message", check=message_channel_author_check, timeout=120.0)
				if message.content in ["done", "Done"]:
					ended = True
					break
				if not message.role_mentions:
					embed.description = "Invalid Role, Please mention a valid role"
					await message.delete()
					await original_message.edit(embed=embed)
				else:
					role = message.role_mentions[0]
					await message.delete()
					emoji_to_insert = None
					while not emoji_to_insert:
						embed.description = "Please react to this message with the emoji you wish to use"
						await original_message.edit(embed=embed)
						reaction, user = await self.bot.wait_for("reaction_add", check=react_channel_author_check,
						                                         timeout=120.0)
						emoji = reaction.emoji
						if isinstance(emoji, str):
							emoji_to_insert = emoji
						else:
							emoji_from_bot = self.bot.get_emoji(emoji.id)
							if not emoji_from_bot:
								embed.description = "I can't find emoji in any of the guilds I'm in"
								await original_message.edit(embed=embed)
							else:
								emoji_to_insert = str(emoji.id)

						if emoji_to_insert:
							roles.append((role, emoji_to_insert))
							embed.description = "Mention another role to add a role or type `done`"
							await original_message.clear_reactions()
							await original_message.edit(embed=embed)

		if not roles:
			embed.description = "No roles added. I will now exit"
			await original_message.edit(embed=embed)
			return

		chunks = [roles[x:x+9] for x in range(0, len(roles), 10)]

		for chunk in chunks:
			embed = Embed(title="Self Assignable Roles")
			emojis = []
			for role in chunk:
				embed.add_field(name=role[0].name, value=role[1])
				emojis.append(role[1])
			role_message = await channel.send(embed=embed)
			query = "INSERT INTO react_roles (message_id, role_id, emoji_id, guild_id) VALUES ($1, $2, $3, $4)"
			for role in chunk:
				await self.bot.pool.execute(query, role_message.id, role[0].id, role[1], ctx.guild.id)

	@commands.command(aliases=['add_react_roles'])
	@checks.is_admin()
	async def add_react_role(self, ctx, message_id: int, role: Role):
		"""Add a ReactRole. Provide the message ID of the message to be reacted to and the role of the one you want to grant"""

		got_emoji = False
		while not got_emoji:
			reaction_request_message = await ctx.send(
				embed=self.bot.notice(f'React to this message with the desired emoji for {role.mention}'))

			def react_check(check_reaction, check_user):
				return (check_reaction.message.id == reaction_request_message.id) and (check_user == ctx.author)

			try:
				reaction, user = await self.bot.wait_for('reaction_add', check=react_check, timeout=120.0)
			except Exception as e:
				return

			emoji = reaction.emoji
			if isinstance(emoji, str):
				emoji_to_insert = emoji
			else:
				emoji_from_bot = self.bot.get_emoji(emoji.id)
				if not emoji_from_bot:
					await ctx.send(embed=self.bot.error("I can't find emoji in any of the guilds I'm in"))
					return
				else:
					emoji_to_insert = str(emoji.id)

		query = "INSERT INTO react_roles (message_id, role_id, emoji_id, guild_id) VALUES ($1, $2, $3, $4)"
		await self.bot.pool.execute(query, message_id, role.id, emoji_to_insert, ctx.guild.id)
		await ctx.send(embed=self.bot.success(f"Emoji set to {emoji} for {role.name}"))

	@commands.command(aliases=['view_react_role'])
	@checks.is_admin()
	async def view_react_roles(self, ctx):
		"""See all active ReactRoles"""

		query = "SELECT * FROM react_roles WHERE guild_id = $1"
		results = await self.bot.pool.fetch(query, ctx.guild.id)
		results = list(results)

		react_role_dict = {}
		for key, items in itertools.groupby(results, operator.itemgetter('message_id')):
			react_role_dict[key] = list(items)

		embed = Embed(title="Reaction Roles for {}".format(ctx.guild))
		for message_id, reactroles in react_role_dict.items():
			items_string = ""
			for reactrole in reactroles:
				try:
					emoji = self.bot.get_emoji(int(reactrole['emoji_id']))
					if emoji:
						emoji_string = "<{}:{}:{}>".format("a" if emoji.animated else "", emoji.name, emoji.id)
					else:
						emoji_string = "EMOJI NOT FOUND"
				except ValueError as e:
					emoji_string = reactrole['emoji_id']
				role = utils.get(ctx.guild.roles, id=reactrole["role_id"])
				if role:
					role = role.mention
				else:
					role = "Role not found role ID: {}".format(reactrole["role_id"])
				items_string += "Reaction {} for role {}\n".format(emoji_string, role)
			embed.add_field(name="Roles for message id: {}".format(message_id), value=items_string)

		await ctx.send(embed=embed)

	@commands.command(aliases=['delete_react_roles'])
	@commands.guild_only()
	@checks.is_admin()
	async def delete_react_role(self, ctx):
		"""Delete a ReactRole"""

		query = "SELECT * FROM react_roles WHERE guild_id = $1"
		results = await self.bot.pool.fetch(query, ctx.guild.id)
		results = list(results)

		react_role_dict = {}
		for key, items in itertools.groupby(results, operator.itemgetter('message_id')):
			react_role_dict[key] = list(items)

		counter = 1
		delete_temp = []
		embed = Embed(title="Reaction Roles for {}".format(ctx.guild),
		              description="Reply with the number of the ReactRole you would like to remove")
		for message_id, reactroles in react_role_dict.items():
			items_string = ""
			for reactrole in reactroles:
				try:
					emoji = self.bot.get_emoji(int(reactrole['emoji_id']))
					if emoji:
						emoji_string = "<{}:{}:{}>".format("a" if emoji.animated else "", emoji.name, emoji.id)
					else:
						emoji_string = "EMOJI NOT FOUND"
				except ValueError as e:
					emoji_string = reactrole['emoji_id']
				role = utils.get(ctx.guild.roles, id=reactrole["role_id"])
				if role:
					role = role.mention
				else:
					role = "Role not found role ID: {}".format(reactrole["role_id"])
				items_string += "{}. Reaction {} for role {}\n".format(counter, emoji_string, role)
				delete_temp.append(reactrole)
				counter += 1
			embed.add_field(name="Roles for message id: {}".format(message_id), value=items_string)

		await ctx.send(embed=embed)

		def check(m):
			return (m.author == ctx.author) and (m.channel == ctx.channel)

		try:
			choice = await self.bot.wait_for('message', check=check, timeout=120.0)
		except Exception as e:
			return

		try:
			chosen_delete = delete_temp[int(choice.content)-1]
		except Exception as e:
			await ctx.send(embed=self.bot.error('Invalid response... closing... '))
			return

		message_id = chosen_delete["message_id"]
		role_id = chosen_delete["role_id"]

		query = "DELETE FROM react_roles WHERE id IN (SELECT id FROM reactroles WHERE message_id = $1 and role_id = $2 LIMIT 1)"
		await self.bot.pool.execute(query, message_id, role_id)
		await ctx.send(embed=self.bot.success("ReactRole Removed"))

	async def on_raw_reaction_add(self, payload):

		emoji = payload.emoji
		message_id = payload.message_id
		user_id = payload.user_id

		if emoji.is_custom_emoji():
			compare_emoji = str(emoji.id)
		else:
			compare_emoji = emoji.name

		query = "SELECT * FROM react_roles WHERE message_id = $1"
		results = await self.bot.pool.fetch(query, message_id)

		if not results:
			return

		for result in results:
			if compare_emoji == result['emoji_id']:
				guild = self.bot.get_guild(result['guild_id'])
				member = guild.get_member(user_id)
				if member:
					role = utils.get(guild.roles, id=result["role_id"])
					if role:
						await member.add_roles(role)

	async def on_raw_reaction_remove(self, payload):

		emoji = payload.emoji
		message_id = payload.message_id
		user_id = payload.user_id

		if emoji.is_custom_emoji():
			compare_emoji = str(emoji.id)
		else:
			compare_emoji = emoji.name

		query = "SELECT * FROM react_roles WHERE message_id = $1"
		results = await self.bot.pool.fetch(query, message_id)

		if not results:
			return

		for result in results:
			if compare_emoji == result['emoji_id']:
				guild = self.bot.get_guild(result['guild_id'])
				member = guild.get_member(user_id)
				if member:
					role = utils.get(guild.roles, id=result["role_id"])
					if role:
						await member.remove_roles(role)


def setup(bot):
	cog = ReactRoles(bot)
	bot.add_cog(cog)
