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
from threading import Thread

class Website:
	"""The Welcome Related Commands"""

	def __init__(self, bot):
		self.bot = bot
		self.app = Quart(__name__)

		
	def start_app(self):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		self.app.run(port=80)


	@commands.command()
	@checks.is_developer()
	async def run_app(self, ctx):


		
		@self.app.route('/')
		async def index(self):
			return "page"
		
		t = Thread(target=self.start_app)
		t.start()

		await ctx.send("running")



def setup(bot):
    bot.add_cog(Website(bot))





