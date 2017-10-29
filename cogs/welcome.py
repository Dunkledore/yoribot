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
		"""Tells you command usage stats for the server or a member."""
		await ctx.send('Will ask for message')
		await self.show_welcome_message(ctx)

	async def show_welcome_message(self, ctx):
		embed = discord.Embed(title='Welcome Message', colour=discord.Colour.blurple())
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		await ctx.send('about to query')
		embed.add_field(name='Testing', value='testin')
		await ctx.send('line')
		await ctx.send(embed=embed)

		try:
			welcome = await ctx.db.fetchrow(query, ctx.guild.id)
			await ctx.send('done')
			await ctx.send(welcome[0])
		except Exception as e:
			await ctx.send(e)
		


def setup(bot):
    bot.add_cog(Welcome(bot))




