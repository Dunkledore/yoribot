import discord 
from discord.ext import commands
from quart import Quart, g, session, render_template, redirect, request
from requests_oauthlib import OAuth2Session
import os
import asyncio
from multiprocessing.pool import ThreadPool
from . import config
import functools
from .utils import checks

class Website:
	"""The Welcome Related Commands"""

	def __init__(self, bot):
		self.bot = bot
		self.app = Quart(__name__)

		
	@commands.command()
	@checks.is_developer()
	async def run_app(self, ctx):
		#self.app.add_url_rule('/', 'index,', self.index)
		func = functools.partial(self.app.run, port=80)
		await self.bot.loop.run_in_executor(None, func)

	@self.app.route('/')
	async def index(self):
		return "page"

def setup(bot):
    bot.add_cog(Website(bot))





