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
		await self.show_welcome_message(ctx)

	async def show_welcome_message(self, ctx):
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await ctx.db.fetch(query, ctx.guild.id)
		embed = discord.Embed(title='User Joined', colour=discord.Colour.blurple())
		await ctx.send(embed=embed)
		#embed.add_field(name='User', value=ctx.message.author.mention)

		#for fields in welcome:
		#	embed.addfield()

		await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))




