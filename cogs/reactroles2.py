import discord
from discord.ext import commands
from .utils import checks
import itertools
import operator

class ReactRoles:

	def __init__(self, bot):
		self.bot = bot


	@commands.command()
	@checks.is_admin()
	async def add_react_role(self, ctx, message_id: int, role : discord.Role):

		
		reaction_request_message = await ctx.send("Please react to this message with the desired Emoji for that role")

		def react_check(reaction, user):
			return (reaction.message.id == reaction_request_message.id and user == ctx.author)
		
		reaction, user = await self.bot.wait_for('reaction_add', check=react_check, timeout=120.0)

		emoji = reaction.emoji

		query = "INSERT INTO reactroles (message_id, role_id, emoji_id, guild_id) VALUES ($1, $2, $3, $4)"
		await self.bot.pool.execute(query, message_id, role.id, str(emoji.id) or str(emoji) , ctx.guild.id)
		await ctx.send("Emoji set to {} for {}".format(emoji, role.name))

	@commands.command()
	@checks.is_admin()
	async def view_react_roles(self, ctx):

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
				items_string += "Reaction {} for role {}".format(reactrole['emoji_id'], reactrole['role_id'])
			embed.add_field(name="Roles for message id: {}".format(message_id), value=items_string)

		await ctx.send(embed)

	async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):

		query = "SELECT * FROM reactroles WHERE message_id = $1"
		results = await self.bot.pool.fetch(query, message_id)

		if not results:
			return

		for result in results:
			if (emoji.id or str(emoji)) == result['emoji_id']:
				guild = self.bot.get_guild(result['guild_id'])
				member = guild.get_member("user_id")
				if member:
					role = discord.utils.get(guild.roles, id=results["role_id"])
					if role:
						await member.add_roles(role)


def setup(bot):
	cog = ReactRoles(bot)
	bot.add_cog(cog)



















