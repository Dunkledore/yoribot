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
		await ctx.send('this')
		await self.show_welcome_message(ctx)

	async def show_welcome_message(self, ctx):
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await ctx.db.fetch(query, ctx.guild.id)
		#title = 'Welcome to ' + ctx.message.server.name
		#await ctx.send(title)
		embed = discord.Embed(title='Welcome to ' + ctx.message.guild.name, colour=discord.Colour.blurple())
		
		embed.add_field(name='User', value=ctx.message.author.mention)


		for fields in welcome:
			embed.add_field(name=fields[2], value=fields[3])
		#for fields in welcome:
		#	embed.addfield(name=welcome[2], value=welcome[3])


		await ctx.send(embed=embed)

	@commands.command()
	@checks.is_mod()
	async def addfield(ctx, arg1, arg2):
		
		await ctx.send('testing')
		if (arg1 is None) or (arg2 is None):
			await ctx.send('Please enter both a field and a value')
		else:
			query = "INSERT INTO welcome (guild_id, name, value) VALUES ($1, $2, &3)"
			ctx.db.execute(query, ctx.guiild.id, arg1, arg2)
			await ctx.send('added')




	




def setup(bot):
    bot.add_cog(Welcome(bot))




