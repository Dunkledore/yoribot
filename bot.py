import asyncio
import datetime
import os
import sys
import traceback
from datetime import datetime
from threading import Thread
import inspect
from discord.ext.commands import Command

import aiohttp
import asyncpg
from discord import Embed, Forbidden
from discord.ext import commands

from cogs.utils import utils, dataIO
from cogs.website import Website
from instance import token, new_server_hook, error_hook, db_uri, root_website, client_secret, port, client_id, redirect

initial_cogs = ["developers"]


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
		self.website = Website(client_secret, client_id, redirect, port, self)

	def run_website(self):
		asyncio.set_event_loop(self.loop)
		try:
			self.website.run()
		except Exception as error:
			print(error)

	async def __ainit__(self):

		self.pool = await asyncpg.create_pool(db_uri)

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
		elif isinstance(error, Forbidden):
			await ctx.send(embed=self.error("I don't have permissions to do this"))
		elif isinstance(error, commands.CommandOnCooldown):
			if not hasattr(ctx.command, 'on_error'):
				await ctx.send(embed=self.error('You are on cooldown. Try again in {:.2f}s'.format(error.retry_after)))
		elif not isinstance(error, (commands.CheckFailure,
		                            commands.CommandNotFound,
		                            commands.UserInputError)):
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

	def add_cog(self, cog):  # This has only been overwritten for the sake of adding cog categories
		self.cogs[type(cog).__name__] = cog

		try:
			check = getattr(cog, '_{.__class__.__name__}__global_check'.format(cog))
		except AttributeError:
			pass
		else:
			self.add_check(check)

		try:
			check = getattr(cog, '_{.__class__.__name__}__global_check_once'.format(cog))
		except AttributeError:
			pass
		else:
			self.add_check(check, call_once=True)

		try:
			category = getattr(cog, "category")
			if category in self.categories:
				self.categories[category].append(type(cog).__name__)
			else:
				self.categories[category] = [type(cog).__name__]
		except AttributeError:
			pass

		members = inspect.getmembers(cog)
		for name, member in members:
			# register commands the cog has
			if isinstance(member, Command):
				if member.parent is None:
					self.add_command(member)
				continue

			# register event listeners the cog has
			if name.startswith('on_'):
				self.add_listener(member, name)

	def remove_cog(self, name):

		cog = self.cogs.pop(name, None)
		if cog is None:
			return

		members = inspect.getmembers(cog)
		for name, member in members:
			# remove commands the cog has
			if isinstance(member, Command):
				if member.parent is None:
					self.remove_command(member.name)
				continue

			# remove event listeners the cog has
			if name.startswith('on_'):
				self.remove_listener(member)

		try:
			check = getattr(cog, '_{0.__class__.__name__}__global_check'.format(cog))
		except AttributeError:
			pass
		else:
			self.remove_check(check)

		try:
			check = getattr(cog, '_{0.__class__.__name__}__global_check_once'.format(cog))
		except AttributeError:
			pass
		else:
			self.remove_check(check)

		try:
			category = getattr(cog, "category")
			self.categories[category].remove(type(cog).__name__)
			if not self.categories[category]:
				self.categories.pop(category)
		except AttributeError:
			pass

		unloader_name = '_{0.__class__.__name__}__unload'.format(cog)
		try:
			unloader = getattr(cog, unloader_name)
		except AttributeError:
			pass
		else:
			unloader()

		del cog

	def run(self):
		super().run(token, reconnect=True)
