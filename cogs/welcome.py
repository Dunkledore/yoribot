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
		embed.set_author(name=ctx.message.author.mention, icon_url=member.avatar_url)
		embed.add_field(name='User', value=ctx.message.author.mention)


		for fields in welcome:
			embed.add_field(name=fields[2], value=fields[3])
		#for fields in welcome:
		#	embed.addfield(name=welcome[2], value=welcome[3])


		await ctx.send(embed=embed)

	@commands.command()
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
	async def removefield(self, ctx, arg1=None):

		if arg1 is None:
			await ctx.send('Please enter a field to remove')
		else:
			query = "DELETE FROM welcome WHERE guild_id =$1 AND name = $2"
			await ctx.db.execute(query, ctx.guild.id, arg1)
			await ctx.send('Field Removed')



	




def setup(bot):
    bot.add_cog(Welcome(bot))




