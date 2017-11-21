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

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
	async def welcome(self, ctx):
		"""Will send the welcome message as if the caller just joined"""
		await self.show_welcome_message(ctx)

	async def show_welcome_message(self, ctx):
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await ctx.db.fetch(query, ctx.guild.id)
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name='Welcome to ' + ctx.message.guild.name + ' ' + ctx.message.author.name, icon_url=ctx.message.guild.icon_url)
		embed.set_thumbnail(url=ctx.message.author.avatar_url)

		for fields in welcome:
			embed.add_field(name=fields[2], value=fields[3].format(ctx.message.author))


		await ctx.send(embed=embed)

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
	async def welcomeadd(self, ctx, name=None, *, value=None):
		"""Adds an embed field onto the welcome message"""
		
		if (name is None) or (value is None):
			await ctx.send('Please enter both a field and a value')
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

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
	async def welcomeremove(self, ctx, name=None):
		"""Removes and embed field from the welcome message"""

		if name is None:
			await ctx.send('Please enter a field to remove')
			return
		else:
			query = "DELETE FROM welcome WHERE guild_id =$1 AND name = $2"
			await ctx.db.execute(query, ctx.guild.id, name)
			await ctx.send('Field Removed')

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
	async def setwelcomechannel(self, ctx, channel: discord.TextChannel):
		"""Use in the channel you want to set as the welcome channel"""

		insertquery = "INSERT INTO welcome_config (guild_id, channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE welcome_config SET channel_id = $2 WHERE guild_id = $1"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, channel.id)
		await ctx.send('Channel set')


	async def on_member_join(self, member):

		query = "SELECT * FROM welcome_config WHERE guild_id = $1"
		con = self.bot.pool
		chid = await con.fetchrow(query, member.guild.id)
		ch = self.bot.get_channel(chid[2])
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await con.fetch(query, member.guild.id)
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name='Welcome to ' + member.guild.name + ' ' + member.name, icon_url=member.guild.icon_url)
		embed.set_thumbnail(url=member.avatar_url)


		for fields in welcome:
			embed.add_field(name=fields[2], value=fields[3].format(member))


		await ch.send(embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))




