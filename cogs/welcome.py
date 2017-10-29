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

	@commands.group(invoke_without_command=True)
	@commands.guild_only()
	async def welcome(self, ctx, *, member: discord.Member = None):
		"""Will sennd the """
		await self.show_welcome_message(ctx)

	async def show_welcome_message(self, ctx):
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await ctx.db.fetch(query, ctx.guild.id)
		#title = 'Welcome to ' + ctx.message.server.name
		#await ctx.send(title)
		embed = discord.Embed(title='Welcome to ' + ctx.message.guild.name, colour=discord.Colour.blurple())
		embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
		embed.add_field(name='User', value=ctx.message.author.mention)


		for fields in welcome:
			embed.add_field(name=fields[2], value=fields[3])


		await ctx.send(embed=embed)

	@commands.command()
	"""Adds an embed field onto the welcome message"""
	async def addfield(self, ctx, arg1=None, arg2=None):
		
		if (arg1 is None) or (arg2 is None):
			await ctx.send('Please enter both a field and a value')
		else:
			query = "INSERT INTO welcome (guild_id, name, value) VALUES ($1, $2, $3)"
		
		try:
			await ctx.db.execute(query, ctx.guild.id, arg1, arg2)
		except Exception as e:
			await ctx.send('Tag could not be created')
			await ctx.send(e)
		else:
			await ctx.send(f'Field {arg1} successfully created.')

	@commands.command()
	"""Removes and embed field from the welcome message"""
	async def removefield(self, ctx, arg1=None):

		if arg1 is None:
			await ctx.send('Please enter a field to remove')
		else:
			query = "DELETE FROM welcome WHERE guild_id =$1 AND name = $2"
			await ctx.db.execute(query, ctx.guild.id, arg1)
			await ctx.send('Field Removed')

	@commands.command()
	async def setbroadcastchannel(self, ctx):
	"""Use in the channel you want to set as the welcome channel"""

		query = "INSERT INTO welcome_config (guild_id, channel_id) VALUES ($1, $2)"
		await ctx.db.execute(query, ctx.guild.id, ctx.message.channel.id)
		await ctx.send('Channel set')

	async def on_member_join(self, member):

		query = "SELECT * FROM welcome_config WHERE guild_id = $1"
		con = self.bot.pool
		chid = await con.fetchrow(query, member.guild.id)
		print(con)
		print('channel id')
		print(chid[2])
		ch = self.bot.get_channel(chid[2])
		print(ch)
		
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await con.fetch(query, member.guild.id)
		embed = discord.Embed(title='Welcome to ' + member.guild.name, colour=discord.Colour.blurple())
		embed.set_author(name=member.name, icon_url=member.avatar_url)
		embed.add_field(name='User', value=member.mention)


		for fields in welcome:
			embed.add_field(name=fields[2], value=fields[3])


		await ch.send(embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))




