import asyncpg
import discord
from discord.ext import commands
import asyncio
import datetime

from ..utils import checks


class Welcome:
	"""The Welcome Related Commands"""

	def __init__(self, bot):
		self.bot = bot
		self.category = "Admin and Moderation"

	@commands.command()
	@checks.is_admin()
	@commands.guild_only()
	async def welcome(self, ctx):
		"""Test your welcome message"""

		member = ctx.author
		channel = ctx.message.channel

		query = "SELECT * FROM welcome_config WHERE guild_id = $1"
		config = await self.bot.pool.fetchrow(query, member.guild.id)
		if not config:
			await ctx.send(embed=self.bot.error("Welcome settings not setup for this guild"))
			return

		query = "SELECT * FROM welcome_fields WHERE guild_id = $1;"
		welcome_fields = await self.bot.pool.fetch(query, member.guild.id)
		if (not welcome_fields) and (not config["text_message"]):
			await ctx.send(embed=self.bot.error("Welcome message not setup for this guild"))
			return

		# Want to make the embed before sending the text message to increase chances or messages deliver consecutively
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name=f'Welcome to {member.guild.name}', icon_url=member.guild.icon_url)
		embed.set_thumbnail(url=member.avatar_url)

		for fields in welcome_fields:
			embed.add_field(name=fields["name"], value=fields["value"].format(member))

		if config["text_message"]:
			await channel.send(config["text_message"].format(member))

		if welcome_fields:
			await channel.send(embed=embed)

	@commands.command(laliases=['welcome_add', 'add_welcome', "addwecome"])
	@checks.is_admin()
	@commands.guild_only()
	async def welcomeadd(self, ctx, title=None, *, content=None):
		"""Adds a section with a title to your welcome message - for titles with more than one word use quotation marks."""

		if (title is None) or (content is None):
			await ctx.send(embed=self.bot.error('Please enter both title and content'))
			return
		elif len(title) > 256:
			await ctx.send(embed=self.bot.error("Field titles must be 256 characters or shorter"))
			return
		elif len(content) > 1024:
			await ctx.send(embed=self.bot.error("Field content must be 1024 characters or shorter"))
			return
		else:
			query = "INSERT INTO welcome_fields (guild_id, name, value) VALUES ($1, $2, $3)"
			await self.bot.pool.execute(query, ctx.guild.id, title, content)
			await ctx.send(embed=self.bot.success(f'Field {title} successfully created.'))

	@commands.command(aliases=["welcome_remove", "remove_welcome", "removewelcome"])
	@checks.is_admin()
	@commands.guild_only()
	async def welcomeremove(self, ctx, *, section_title):
		"""Removes a section from the welcome message"""
		query = "DELETE FROM welcome_fields WHERE (guild_id =$1) AND (name = $2) RETURNING *"
		deleted = await self.bot.pool.execute(query, ctx.guild.id, section_title)
		if deleted:
			await ctx.send(embed=self.bot.success('Field Removed'))
		else:
			await ctx.send(embed=self.bot.error("No section with that title"))

	async def do_setwelcomechannel(self, guild_id, channel_id):
		insertquery = "INSERT INTO welcome_config (guild_id, channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE welcome_config SET channel_id = $2 WHERE guild_id = $1"

		try:
			await self.bot.pool.execute(insertquery, guild_id, channel_id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, guild_id, channel_id)


	@commands.command(aliases=["set_welcome_channel","welcome_channel_set", "welcomechannelset"])
	@checks.is_admin()
	@commands.guild_only()
	async def setwelcomechannel(self, ctx, channel: discord.TextChannel):
		"""Select the channel you wish the welcome message to appear in"""

		await self.do_setwelcomechannel(ctx.guild.id, channel.id)
		await ctx.send(embed=self.bot.success('Channel set'))


	@commands.command(aliases=["welcome_text"])
	@checks.is_admin()
	@commands.guild_only()
	async def welcometext(self, ctx, *, text=None):
		"""Set a non-embed welcome message - this can be combined with the embed so you can use mentions. Use {0.mention} to mention the user joining and {0.name} to simply say their name. Leave text blank to remove the text"""

		insertquery = "INSERT INTO welcome_config (guild_id, text_message) VALUES ($1, $2)"
		alterquery = "UPDATE welcome_config SET text_message = $2 WHERE guild_id = $1"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, text)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, ctx.guild.id, text)

		if text:
			await ctx.send(embed=self.bot.success('Message set'))
		else:
			await ctx.send(embed=self.bot.success('Message removed'))

	@commands.command(aliases=['no_welcome', 'stop_welcome', 'welcome_stop'])
	@checks.is_admin()
	@commands.guild_only()
	async def nowelcome(self, ctx):
		"""Stop welcome messages entirely."""

		query = "DELETE FROM welcome_config WHERE guild_id = $1"
		await self.bot.pool.execute(query, ctx.guild.id)
		await ctx.send(embed=self.bot.success(f"Welcome message will now no longer send when a member joins"))

	async def do_welcome_whisper(self, guild_id):
		alterquery = "UPDATE welcome_config SET whisper = NOT whisper WHERE guild_id = $1 RETURNING whisper"
		insertquery = "INSERT INTO welcome_config (guild_id, whisper) VALUES ($1,True) RETURNING whisper"
		try:
			whisper = await self.bot.pool.fetchval(insertquery, guild_id)
		except asyncpg.UniqueViolationError:
			whisper = await self.bot.pool.fetchval(alterquery, guild_id)

		return whisper

	@commands.command(hidden=True)
	@checks.is_admin()
	@commands.guild_only()
	async def captcha_role(self, ctx, role: discord.Role):
		"""Set the role to be assigned when the emoji is clicked"""

		alterquery = "UPDATE welcome_config SET captcha_role = $1 WHERE guild_id = $2"
		insertquery = "INSERT INTO welcome_config (guild_id, captcha_role) VALUES ($1,$2)"
		try:
			await self.bot.pool.fetchval(insertquery, role.id, ctx.guild.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.fetchval(alterquery, ctx.guild.id, role.id)

		await ctx.send(embed=self.bot.success(f"Role set to {role.mention}"))

	@commands.command(hidden=True)
	@checks.is_admin()
	@commands.guild_only()
	async def toggle_captcha(self, ctx):
		"""Toggles whether captcha is on or off"""
		alterquery = "UPDATE welcome_config SET whisper = NOT whisper WHERE guild_id = $1 RETURNING whisper"
		insertquery = "INSERT INTO welcome_config (guild_id, whisper) VALUES ($1,True) RETURNING whisper"
		try:
			whisper = await self.bot.pool.fetchval(insertquery, ctx.guild_id)
		except asyncpg.UniqueViolationError:
			whisper = await self.bot.pool.fetchval(alterquery, ctx.guild_id)

		return whisper

	@commands.command(aliases=["welcome_whisper", "whisperwelcome", "whisper_welcome"])
	@checks.is_admin()
	@commands.guild_only()
	async def welcomewhisper(self, ctx):
		"""Toggle sending a direct message to the member on join"""
		whisper = await self.do_welcome_whisper(ctx.guild.id)
		await ctx.send(embed=self.bot.success(f"Whisper set to {whisper}"))

	async def on_member_join(self, member):

		if member.guild.id == 250309924096049164:   #LFG anti-bot
			created = (datetime.datetime.utcnow()-member.created_at).total_seconds()//60
			if created < 60:
				avatars = [f"https://cdn.discordapp.com/embed/avatars/{x}.png" for x in range(0, 10)]
				if member.avatar_url in avatars:
					await member.send(f"Hi {member.mention}\n\nTerribly sorry, however for security reasons we require people joining LFG to have at least added a profile picture to their Discord account. \n\nOnce you add a profile picture please feel free to rejoin at: https://discord.gg/sm87x3F")
					await member.kick()
					return

		query = "SELECT * FROM welcome_config WHERE guild_id = $1"
		config = await self.bot.pool.fetchrow(query, member.guild.id)
		if config is None:
			return

		query = "SELECT * FROM welcome_fields WHERE guild_id = $1;"

		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name='Welcome to '+member.guild.name+' '+member.name, icon_url=member.guild.icon_url)
		embed.set_thumbnail(url=member.avatar_url)
		welcome_message = None

		welcome_fields = await self.bot.pool.fetch(query, member.guild.id)
		for fields in welcome_fields:
			embed.add_field(name=fields["name"], value=fields["value"].format(member))

		if config["whisper"]:
			if config["text_message"]:
				await member.send(config["text_message"].format(member))
			if welcome_fields:
				await member.send(embed=embed)

		welcome_channel = self.bot.get_channel(config["channel_id"])
		if welcome_channel:
			if config["text_message"]:
				await welcome_channel.send(config["text_message"].format(member))
			if welcome_fields:
				welcome_message = await welcome_channel.send(embed=embed)

		def check(left_member):
			return left_member.id == member.id
		try:
			member = await self.bot.wait_for("member_remove", check=check, timeout=7200)
			embed.colour = discord.Color.red()
			await welcome_message.edit(embed=embed)
		except asyncio.TimeoutError:
			pass




def setup(bot):
	bot.add_cog(Welcome(bot))
