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

	def __init__(self, bot):
		self.bot = bot

	async def get_welcomemessage(self, guild_id, name, * , connection=None):
		con = connection or self.bot.pool
		query = """SELECT * 
				   FROM welcome
				   WHERE server_id = $1
				"""
		array = await con.fetch(query, guild_id)

		if array is None:
			e = discord.Embed(title='No embed made', color = 0xdd5f53)
			return e
		else:
			return None
			




