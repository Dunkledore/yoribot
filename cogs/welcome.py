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


	@commands.command()
	async def welcome(self, ctx):
		await ctx.send('trying')
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
				

		await ctx.send(query)
		array = await ctx.db.fetch(query, ctx.guild.id)

		await ctx.send(query)


		if array is None:
			e = discord.Embed(title='No embed made', color = 0xdd5f53)
			await ctx.send(e)
		else:
			await ctx.send('there is one')
			
def setup(bot):
    bot.add_cog(Welcome(bot))



