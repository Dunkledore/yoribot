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


	@commands.command(pass_context=True, no_pm=True)
	async def welcome(self, ctx :commands.Context):
		await ctx.send('trying')
		query = """SELECT * 
				   FROM welcome
				   WHERE server_id = $1
				"""
		array = await ctx.db.fetch(query, ctx.guild_id)

		if array is None:
			e = discord.Embed(title='No embed made', color = 0xdd5f53)
			await ctx.send(e)
		else:
			await ctx.send('there is one')
			
def setup(bot: commands.Bot):
    bot.add_cog(Welcome(bot))



