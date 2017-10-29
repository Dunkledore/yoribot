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
		embed = discord.Embed(title='Welcome Message', colour=discord.Colour.blurple())
		query = "SELECT * FROM welcome WHERE guild_id = $1;"
		welcome = await ctx.db.fetch(query, ctx.guild.id)
		embed.add_field(name='Something' value='value', inline=true)
		await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Welcome(bot))




