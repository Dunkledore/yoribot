import datetime
import os
import sys
import traceback
import asyncio
from datetime import datetime
from threading import Thread

import aiohttp
import asyncpg
from discord import Embed, Forbidden
from discord.ext import commands
from quart import Quart
from cogs.website import add_views

from cogs.utils import utils, dataIO
from instance import token, new_server_hook, error_hook, db_uri, root_website, client_secret, port

initial_cogs = ["developers",
                "logs",
                "prefix",
                "statistics",
                "utilities",
                ]


def _prefix_callable(bot, msg):
	user_id = bot.user.id
	base = [f'<@!{user_id}> ', f'<@{user_id}> ']
	if msg.guild is None:
		base.append('*')
	else:
		base.extend(bot.prefixes.get(str(msg.guild.id), ['*']))
	return base


class YoriBot(commands.AutoShardedBot):

	def __init__(self):
		super().__init__(command_prefix=_prefix_callable, description="YoriBot",
		                 pm_help=None, help_attrs=dict(hidden=True))

		if not os.path.exists("data/prefixes/"):
			os.makedirs("data/prefixes")
		if not os.path.exists("data/prefixes/prefixes.json"):
			dataIO.save_json("data/prefixes/prefixes.json", {})
		self.prefixes = dataIO.load_json("data/prefixes/prefixes.json")

		self.session = aiohttp.ClientSession(loop=self.loop)
		self.error_hook = utils.get_webhook(error_hook, self.session)
		self.new_server_hook = utils.get_webhook(new_server_hook, self.session)

		self.loop.create_task(self.__ainit__())
		self.categories = {}

		self.root_website = root_website
		self.website = Quart(__name__, static_folder="website/static", template_folder="website/templates")
		self.website.config['SECRET_KEY'] = client_secret
		add_views(self.website)


	def run_website(self):
		asyncio.set_event_loop(self.loop)
		self.website.run(host='0.0.0.0', port=port)

	async def __ainit__(self):

		#self.pool = await asyncpg.create_pool(db_uri)

		for extension in initial_cogs:
			try:
				self.load_extension("cogs."+extension)
			except Exception as e:
				print(f'Failed to load extension {extension}.', file=sys.stderr)
				traceback.print_exc()

	def save_prefixes(self):
		dataIO.save_json("data/prefixes/prefixes.json", self.prefixes)

	@staticmethod
	def success(description):
		embed = Embed(color=0x2ecc71,
		              title="✅ Success",
		              description=description)
		return embed

	@staticmethod
	def notice(description):
		embed = Embed(color=0xe67e22,
		              title="❕ Notice",
		              description=description)
		return embed

	@staticmethod
	def error(description):
		embed = Embed(color=0xe74c3c,
		              title="⚠ Error",
		              description=description)
		return embed

	async def on_ready(self):
		print("connected")
		if not hasattr(self, 'uptime'):
			self.uptime = datetime.utcnow()
		await self.error_hook.send(embed=self.notice(f'Ready: {self.user} (ID: {self.user.id})'))
		web_thread = Thread(target=self.run_website())
		web_thread.start()

	async def on_resumed(self):
		await self.error_hook.send(embed=self.notice('Resumed...'))

	async def on_message(self, message):
		if message.author.bot:
			return
		await self.process_commands(message)

	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.NoPrivateMessage):
			await ctx.author.send('This command cannot be used in private messages.')
		elif isinstance(error, commands.DisabledCommand):
			await ctx.author.send('Sorry. This command is disabled and cannot be used.')
		elif not isinstance(error, (commands.CheckFailure,
		                            commands.CommandNotFound,
		                            commands.UserInputError,
		                            Forbidden)):
			e = Embed(title='Command Error', colour=0xcc3366)
			e.add_field(name='Command Name', value=ctx.command.qualified_name)
			e.add_field(name='Invoker', value=f'{ctx.author} (ID: {ctx.author.id})')

			fmt = f'Channel: {ctx.channel} (ID: {ctx.channel.id})'
			if ctx.guild:
				fmt = f'{fmt}\nGuild: {ctx.guild} (ID: {ctx.guild.id})'
			e.add_field(name='Location', value=fmt, inline=False)
			exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, 4))
			e.description = f'```py\n{exc}\n```'
			e.timestamp = datetime.utcnow()
			hook = self.error_hook
			await hook.send(embed=e)

	async def on_error(self, event_method, *args, **kwargs):
		print("error")
		print(event_method)
		hook = self.error_hook

		try:
			e = Embed(title=f"Error in on_{event_method}", colour=0xcc3366)
			exc = traceback.format_exc(-4)
			e.description = f"```py\n{exc}\n```"
			e.timestamp = datetime.utcnow()
			await hook.send(embed=e)
		except Exception as e:
			print(e)

	def run(self):
		super().run(token, reconnect=True)
