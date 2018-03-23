import discord
from discord.ext import commands
from .utils import checks
import itertools
import operator
import traceback


#create table reactroles (id SERIAL, message_id bigint, role_id bigint, emoji_id text, guild_id bigint)

class ReactRoles:
	"""Use message reactions to manage selfroles"""

	def __init__(self, bot):
		self.bot = bot


	@commands.command(aliases=['add_react_roles'])
	@checks.is_admin()
	async def add_react_role(self, ctx, message_id: int, role : discord.Role):
		"""Add a ReactRole. Provide the message ID of the message to be reacted to and the role of the one you want to grant"""

		got_emoji = False
		while not got_emoji:
			embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ Notice",
                                description ='React to this message with the desired emoji for {}'.format(role.mention))
			reaction_request_message = await ctx.send(embed=embed)

			def react_check(reaction, user):
				return (reaction.message.id == reaction_request_message.id and user == ctx.author)
			
			try:
				reaction, user = await self.bot.wait_for('reaction_add', check=react_check, timeout=120.0)
			except Exception as e:
				return

			emoji = reaction.emoji
			if isinstance(emoji, str):
				emoji_to_insert = emoji
				got_emoji = True
			else:
				emoji_from_bot = self.bot.get_emoji(emoji.id)
				if not emoji_from_bot:
					embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ="I can't find emoji in any of the guilds I'm in")
					await ctx.send(embed=embed)
					return
				else:
					emoji_to_insert = str(emoji.id)
					got_emoji = True


		query = "INSERT INTO reactroles (message_id, role_id, emoji_id, guild_id) VALUES ($1, $2, $3, $4)"
		await self.bot.pool.execute(query, message_id, role.id, emoji_to_insert, ctx.guild.id)
		embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ="Emoji set to {} for {}".format(emoji, role.name))
		await ctx.send(embed=embed)


	@commands.command(aliases=['view_react_role'])
	@checks.is_admin()
	async def view_react_roles(self, ctx):
		"""See all active ReactRoles"""

		query = "SELECT * FROM reactroles WHERE guild_id = $1"
		results = await self.bot.pool.fetch(query, ctx.guild.id)
		results = list(results)

		react_role_dict = {}
		for key, items in itertools.groupby(results, operator.itemgetter('message_id')):
			react_role_dict[key] = list(items)

		embed = discord.Embed(title="Reaction Roles for {}".format(ctx.guild), description = discord.Embed.Empty)
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
				role = discord.utils.get(ctx.guild.roles, id=reactrole["role_id"])
				if role:
					role = role.mention
				else:
					role = "Role not found role ID: {}".format(reactrole["role_id"])
				items_string += "Reaction {} for role {}\n".format(emoji_string, role)
			embed.add_field(name="Roles for message id: {}".format(message_id), value=items_string)

		await ctx.send(embed=embed)

	@commands.command(aliases=['delete_react_roles'])
	@checks.is_admin()
	async def delete_react_role(self, ctx):
		"""Delete a ReactRole"""

		query = "SELECT * FROM reactroles WHERE guild_id = $1"
		results = await self.bot.pool.fetch(query, ctx.guild.id)
		results = list(results)

		react_role_dict = {}
		for key, items in itertools.groupby(results, operator.itemgetter('message_id')):
			react_role_dict[key] = list(items)

		counter = 1
		delete_temp = []
		embed = discord.Embed(title="Reaction Roles for {}".format(ctx.guild), description = "Reply with the number of the ReactRole you would like to remove")
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
				role = discord.utils.get(ctx.guild.roles, id=reactrole["role_id"])
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
			embed=discord.Embed(color=ctx.message.author.color,
								title = "⚠ Error",
								description ='Invalid response... closing... ' + str(e))
			await ctx.send(embed=embed)
			return

		message_id = chosen_delete["message_id"]
		role_id = chosen_delete["role_id"]

		query = "DELETE FROM reactroles WHERE id IN (SELECT id FROM reactroles WHERE message_id = $1 and role_id = $2 LIMIT 1)"
		await self.bot.pool.execute(query, message_id, role_id)
		embed=discord.Embed(color=ctx.message.author.color,
								title = "✅ Success",
								description ='ReactRole Removed')
		await ctx.send(embed=embed)



	async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):


		if emoji.is_custom_emoji():
			compare_emoji = str(emoji.id)
		else:
			compare_emoji = emoji.name

		query = "SELECT * FROM reactroles WHERE message_id = $1"
		results = await self.bot.pool.fetch(query, message_id)

		if not results:
			return

		for result in results:
			if compare_emoji == result['emoji_id']:
				guild = self.bot.get_guild(result['guild_id'])
				member = guild.get_member(user_id)
				if member:
					role = discord.utils.get(guild.roles, id=result["role_id"])
					if role:
						await member.add_roles(role)

	
	async def on_raw_reaction_remove(self, emoji, message_id, channel_id, user_id):

		if emoji.is_custom_emoji():
			compare_emoji = str(emoji.id)
		else:
			compare_emoji = emoji.name

		query = "SELECT * FROM reactroles WHERE message_id = $1"
		results = await self.bot.pool.fetch(query, message_id)

		if not results:
			return

		for result in results:
			if compare_emoji == result['emoji_id']:
				guild = self.bot.get_guild(result['guild_id'])
				member = guild.get_member(user_id)
				if member:
					role = discord.utils.get(guild.roles, id=result["role_id"])
					if role:
						await member.remove_roles(role)





def setup(bot):
	cog = ReactRoles(bot)
	bot.add_cog(cog)



















