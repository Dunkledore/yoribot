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
import itertools, inspect

def _command_signature(cmd):
	# this is modified from discord.py source
	# which I wrote myself lmao

	result = [cmd.qualified_name]
	if cmd.usage:
		result.append(cmd.usage)
		return ' '.join(result)

	params = cmd.clean_params
	if not params:
		return ' '.join(result)

	for name, param in params.items():
		if param.default is not param.empty:
			# We don't want None or '' to trigger the [name=value] case and instead it should
			# do [name] since [name=None] or [name=] are not exactly useful for the user.
			should_print = param.default if isinstance(param.default, str) else param.default is not None
			if should_print:
				result.append(f'[{name}={param.default!r}]')
			else:
				result.append(f'[{name}]')
		elif param.kind == param.VAR_POSITIONAL:
			result.append(f'[{name}...]')
		else:
			result.append(f'<{name}>')

	return ' '.join(result)

class Website:
	"""The Welcome Related Commands"""

	def __init__(self, bot):
		self.bot = bot
		self.app = Quart(__name__)

		
	def start_app(self):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		self.app.run(host = '0.0.0.0', port=80)


	@commands.command()
	@checks.is_developer()
	async def run_app(self, ctx):


		
		@self.app.route('/')
		async def index():
			return await render_template('index.html')

		@self.app.route('/commands')
		async def commands():
			cogs = self.get_cogs()
			return await render_template('commands.html', cogs=cogs)
		
		t = Thread(target=self.start_app)
		t.start()

		await ctx.send("running")

	def get_cogs(self):
		
		def key(c):
			return c.cog_name or '\u200bMisc'

		entries = sorted(self.bot.commands, key=key)
		display_commands = []

		# 0: (cog, desc, commands) (max len == 9)
		# 1: (cog, desc, commands) (max len == 9)
		# ...

		for cog, commands in itertools.groupby(entries, key=key):
			non_hidden = [cmd for cmd in commands if not cmd.hidden]
			non_hidden = sorted(non_hidden, key=lambda x: x.name)
			if len(non_hidden) == 0:
				continue

			description = ctx.bot.get_cog(cog)
			if description is not None:
				description = inspect.getdoc(description) or None
			detailed_commands = []

			for command in non_hidden:
				sig = (_command_signature(command))
				desc = command.short_doc or "No help given"
				detailed_commands.append({"signature" : sig, "description" : desc})


			display_commands.append({"name" : cog, "description" : description, "commands" : detailed_commands})

			return display_commands




def setup(bot):
	bot.add_cog(Website(bot))








