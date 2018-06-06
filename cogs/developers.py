from .utils import checks
from discord.ext import commands
import asyncio
from discord import Embed, File, Game
from prettytable import PrettyTable
import time
import io
import traceback
import textwrap
from contextlib import redirect_stdout


class Developers:

	def __init__(self, bot):
		self.bot = bot
		self.divisor = 1
		self.bot.loop.create_task(self.error())
		self.bot.loop.create_task(self.statuses())

	# Database #

	@commands.command(hidden=True)
	@checks.is_developer()
	async def updatetables(self, ctx):
		statements = ["CREATE TABLE IF NOT EXISTS guild_config (guild_id BIGINT PRIMARY KEY, mod_role_id BIGINT, "
		              "admin_role_id BIGINT, greeter_role_id BIGINT)",
		              "CREATE TABLE IF NOT EXISTS statistics (id SERIAL, guild_id BIGINT, channel_id BIGINT, author_id "
		              "BIGINT, time timestamp with time zone DEFAULT current_timestamp, prefix TEXT, command_name TEXT)",
		              "CREATE TABLE IF NOT EXISTS log_config (guild_id BIGINT PRIMARY KEY, member_log_channel_id BIGINT, "
		              "message_log_channel_id BIGINT, invite_log_channel_id BIGINT, participatig BOOL)",
		              "CREATE TABLE IF NOT EXISTS event_logs (id SERIAL, action TEXT, target_id BIGINT, "
		              "user_id BIGINT, guild_id BIGINT, time timestamp with time zone DEFAULT current_timestamp)",
		              "CREATE TABLE IF NOT EXISTS message_logs (message_id BIGINT PRIMARY KEY, content TEXT, author_id "
		              "BIGINT, "
		              "channel_id BIGINT, guild_id BIGINT, status TEXT, time timestamp with time zone DEFAULT current "
		              "timestamp )"
		              ]

		for statement in statements:
			await self.bot.pool.execute(statement)

		await ctx.send(embed=self.bot.success("Tables Updated"))

	@commands.command(hidden=True)
	@checks.is_developer()
	async def sql(self, ctx, *, query: str):
		"""Run some SQL."""

		try:
			start = time.time()
			results = await self.bot.pool.fetch(query)
			end = time.time()
		except Exception:
			return await ctx.send(embed=self.bot.error(f'```py\n{traceback.format_exc()}\n```'))

		if len(results) == 0:
			embed = self.bot.success(f'`{results}`')
			embed.set_footer(text=f'Took {start-end:.2f}ms')
			return await ctx.send(embed=embed)

		headers = list(results[0].keys())
		table = PrettyTable(headers)
		for row in results:
			table.add_row(list(row.values()))
		table = table.get_string()

		fmt = f'```\n{table}\n```'
		if len(fmt) > 2000:
			fmt += f'\n {fmt} Took {start-end:2f}ms'
			fp = io.BytesIO(fmt.encode('utf-8'))
			await ctx.send(embed=self.bot.error('Too many results...'))
			await ctx.send(file=File(fp, 'results.txt'))
		else:
			embed = self.bot.success(fmt)
			embed.set_footer(text=f'Took {start-end:.2}fms')
			await ctx.send(embed=embed)

	# Deliberate Errors #

	@commands.command(hidden=True)
	@checks.is_developer()
	async def testcommanderror(self, ctx):
		await ctx.send(0/0)

	@commands.command(hidden=True)
	@checks.is_developer()
	async def testerror(self, ctx):
		self.divisor = 0
		await asyncio.sleep(10)
		self.divisor = 1

	@commands.command(hidden=True)
	@checks.is_developer()
	async def toolong(self, ctx):
		await ctx.send(",".join([str(x) for x in range(1, 2001)]))

	# Bot Management #

	@commands.command(hidden=True)
	@checks.is_developer()
	async def leave(self, ctx, id: int):
		for guild in self.bot.guilds:
			if id == guild.id:
				await guild.leave()
				return
		await ctx.send(embed=Embed(color=ctx.message.author.color,
		                           title="⚠ Error",
		                           description="You are not in that guild"))

	async def error(self):
		await self.bot.wait_until_ready()
		while True:
			await asyncio.sleep(10)
			x = 1/self.divisor

	async def on_message(self, message):
		if message.content != "enfqihbehbf":
			return

		def func1():
			def func2():
				def func3():
					def fund4():
						def func5():
							x = 1/0

						func5()

					fund4()

				func3()

			func2()

		func1()

	# Other #

	@commands.command(hidden=True)
	@checks.is_developer()
	async def eval(self, ctx, *, body: str):
		"""Evaluates code"""

		if not hasattr(self, '_last_result'):
			self._last_result = None

		env = {
			'bot': self.bot,
			'ctx': ctx,
			'channel': ctx.channel,
			'author': ctx.author,
			'guild': ctx.guild,
			'message': ctx.message,
			'_': self._last_result
		}

		if body.startswith('```') and body.endswith('```'):
			body = '\n'.join(body.split('\n')[1:-1])
		body = body.strip('` \n')
		to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
		try:
			exec(to_compile, env)
		except Exception as e:
			return await ctx.send(embed=self.bot.error(f'```py\n{e.__class__.__name__}: {e}\n```'))

		func = env['func']
		new_out = io.StringIO()
		try:
			with redirect_stdout(new_out):
				ret = await func()
		except Exception as e:
			value = new_out.getvalue()
			await ctx.send(embed=self.bot.error(f'```py\n{value}{traceback.format_exc()}\n```'))
		else:
			value = new_out.getvalue()
			try:
				await ctx.message.add_reaction('\u2705')
			except:
				pass

			if ret is None:
				if value:
					await ctx.send(f'```py\n{value}\n```')
			else:
				self._last_result = ret
				await ctx.send(f'```py\n{value}{ret}\n```')

	async def statuses(self):
		await self.bot.wait_until_ready()
		count = 0
		while True:
			await asyncio.sleep(600)

			presenceText = ""
			if count == 0:
				presenceText = "yoribot.com"
			elif count == 1:
				presenceText = "help | @yori help"
			elif count == 2:
				presenceText = f"on {len(self.bot.guilds)} servers"
			elif count == 3:
				presenceText = f"with {len(self.bot.users)} users"

			await self.bot.change_presence(activity=Game(name=presenceText))
			count = count+1
			if count > 3:
				count = 0


def setup(bot):
	n = Developers(bot)
	bot.add_cog(n)
