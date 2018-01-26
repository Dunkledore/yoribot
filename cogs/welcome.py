from .utils import db, checks, formats, cache
from .utils.paginator import Pages

from discord.ext import commands
import json
import re
import datetime
import discord
import asyncio
import traceback
import asyncpg

class Welcome:
	"""The Welcome Related Commands"""

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def welcome(self, ctx):
		"""Will send the welcome message as if the caller just joined"""
		await self.show_welcome_message(ctx)

	async def show_welcome_message(self, ctx):
		member = ctx.author
		query = "SELECT * FROM welcome_config WHERE guild_id = $1"
		con = self.bot.pool
		config = await con.fetchrow(query, member.guild.id)
		if config is None:
			return
		ch = ctx.message.channel
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await con.fetch(query, member.guild.id)
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name='Welcome to ' + member.guild.name + ' ' + member.name, icon_url=member.guild.icon_url)
		embed.set_thumbnail(url=member.avatar_url)

		for fields in welcome:
			embed.add_field(name=fields["name"], value=fields["value"].format(member))

		if config["text_message"]:
			await ch.send(config["text_message"].format(member))
		await ch.send(embed=embed)


	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def welcomeadd(self, ctx, name=None, *, value=None):
		"""Adds a section with a title to your welcome message - for titles with more than one word use quotation marks."""
		
		if (name is None) or (value is None):
			await ctx.send('Please enter both a field and a value')
			return
		elif len(name) > 256:
			await ctx.send("Field names must be 256 characters or shorter")
			return
		elif len(value) > 1024:
			await ctx.send("Field content must be 1024 characters or shorter")
			return
		else:
			query = "INSERT INTO welcome (guild_id, name, value) VALUES ($1, $2, $3)"
		
		try:
			await ctx.db.execute(query, ctx.guild.id, name, value)
		except Exception as e:
			await ctx.send('Field could not be created')
			await ctx.send(e)
		else:
			await ctx.send(f'Field {name} successfully created.')

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def welcomeremove(self, ctx, name=None):
		"""Removes a section from the welcome message - if the section title has more than one word use quotation marks around them."""

		if name is None:
			await ctx.send('Please enter a field to remove')
			return
		else:
			query = "DELETE FROM welcome WHERE guild_id =$1 AND name = $2"
			await ctx.db.execute(query, ctx.guild.id, name)
			await ctx.send('Field Removed')

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def setwelcomechannel(self, ctx, channel: discord.TextChannel):
		"""Use in the channel you want to set as the welcome channel to designate it as the welcome channel."""

		insertquery = "INSERT INTO welcome_config (guild_id, channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE welcome_config SET channel_id = $2 WHERE guild_id = $1"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, channel.id)
		await ctx.send('Channel set')

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def welcometext(self, ctx, *, text):
		"""Set a non-embed welcome message - this can be combined with the embed so you can use mentions. Use {0.mention} to mention the user joining and {0.name} to simply say their name."""

		insertquery = "INSERT INTO welcome_config (guild_id, text_message) VALUES ($1, $2)"
		alterquery = "UPDATE welcome_config SET text_message = $2 WHERE guild_id = $1"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, text)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, text)
		await ctx.send('Message set')

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def nowelcome(self, ctx):
		"""Stop welcome messages entirely."""


		query = "DELETE FROM welcome_config WHERE guild_id = $1"

		await ctx.db.execute(query, ctx.guild.id)
		
		await ctx.send('I will no longer send a welcome messgae. To re-enable please use. ?setwelcomechannel')


	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def welcomewhisper(self, ctx):
		"""Send the welcome message as a DM instead of in a channel."""
		alterquery = "UPDATE welcome_config SET whisper = NOT whisper WHERE guild_id = $1 RETURNING whisper"
		insertquery = "INSERT INTO welcome_config (guild_id, whisper) VALUES ($1,True)"
		try:
			await ctx.db.execute(insertquery, ctx.guild.id)
			await ctx.send("Whisper set to True")
		except asyncpg.UniqueViolationError:
			whisper = await ctx.db.fetchval(alterquery, ctx.guild.id)
			await ctx.send("Whisper set to " + str(whisper))



	async def on_member_join(self, member):

		query = "SELECT * FROM welcome_config WHERE guild_id = $1"
		con = self.bot.pool
		config = await con.fetchrow(query, member.guild.id)
		if config is None:
			return
		ch = self.bot.get_channel(config["channel_id"])
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await con.fetch(query, member.guild.id)
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name='Welcome to ' + member.guild.name + ' ' + member.name, icon_url=member.guild.icon_url)
		embed.set_thumbnail(url=member.avatar_url)

		for fields in welcome:
			embed.add_field(name=fields["name"], value=fields["value"].format(member))

		if config["whisper"]:
			if config["text_message"]:
				await member.send(config["text_message"].format(member))
			await member.send(embed=embed)
		
		if ch:
			if config["text_message"]:
				await ch.send(config["text_message"].format(member))
			await ch.send(embed=embed)

	@commands.command(hidden=True) #for lgbt youth
	@commands.guild_only()
	@checks.is_admin()
	async def welcomeleavetoggle(self, ctx):
		alterquery = "UPDATE welcome_config SET leave = NOT leave WHERE guild_id = $1 RETURNING leave"
		insertquery = "INSERT INTO welcome_config (guild_id, leave) VALUES ($1,True)"
		try:
			await ctx.db.execute(insertquery, ctx.guild.id)
			await ctx.send("Leave set to True")
		except asyncpg.UniqueViolationError:
			leave = await ctx.db.fetchval(alterquery, ctx.guild.id)
			await ctx.send("Leave set to " + str(leave))

	async def on_member_leave(self, member): #for lgbt youth

		query = "SELECT * FROM welcome_config WHERE guild_id = $1"
		con = self.bot.pool
		config = await con.fetchrow(query, member.guild.id)
		if config is None:
			return
		ch = self.bot.get_channel(config["channel_id"])
		if not config["leave"]:
			return

		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name=member.name + ' left', icon_url=member.guild.icon_url)
		embed.set_thumbnail(url=member.avatar_url)
		
		if ch:
			await ch.send(embed=embed)



		
		

def setup(bot):
    bot.add_cog(Welcome(bot))




