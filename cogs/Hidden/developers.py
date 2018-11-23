import asyncio
import io
import textwrap
import time
import traceback
from contextlib import redirect_stdout
from subprocess import Popen, PIPE, STDOUT

from discord import File, Game, Embed
from discord.ext import commands
from prettytable import PrettyTable

from ..utils import checks


class Developers:

	def __init__(self, bot):
		self.bot = bot
		self.divisor = 1
		self.error_task = self.bot.loop.create_task(self.error())
		self.status_task = self.bot.loop.create_task(self.statuses())

	def __unload(self):
		self.error_task.cancel()
		self.status_task.cancel()

	# Cogs #

	async def on_guild_join(self, guild):
		embed = Embed(title="New Guild", color=0x53dda4)
		embed.add_field(name='Name', value=guild.name)
		embed.add_field(name='ID', value=guild.id)
		embed.add_field(name='Owner', value=guild.owner.mention)
		embed.add_field(name="Guilds Shared With Owner", value="\n".join([botguild.name for botguild in self.bot.guilds if guild.owner in botguild.members]))
		bots = sum(m.bot for m in guild.members)
		members = guild.member_count
		embed.add_field(name='Members', value=str(members))
		embed.add_field(name='Bots', value=str(bots))
		bot_percentage = bots/(bots+members)
		if (bot_percentage >= 0.5) and (bots > 15):
			await self.bot.new_server_hook.send("<@&381072362143219712> High percentage of bots")
		if guild.icon:
			embed.set_thumbnail(url=guild.icon_url)

		if guild.me:
			embed.timestamp = guild.me.joined_at

		message = await self.bot.new_server_hook.send(embed=embed)
		await self.bot.new_server_hook.send(message)
		await message.add_reaction('❌')

		def check(reaction, user):
			return (not user.bot) and (reaction.message.id == message.id) and (reaction.emoji == '❌')

		try:
			reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=86400)
			await guild.leave()
		except asyncio.TimeoutError:
			pass

	async def on_guild_remove(self, guild):
		embed = Embed(colour=0xdd5f53, title='Left Guild')
		embed.add_field(name="Name", value=guild.name)
		members = guild.member_count
		embed.add_field(name="Members", value=members)
		embed.add_field(name="Owner", value=guild.owner.mention)
		await self.bot.new_server_hook.send(embed=embed)


	@commands.command(hidden=True)
	@checks.is_developer()
	async def load(self, ctx, extension):
		try:
			self.bot.load_extension(extension)
		except Exception as e:
			await ctx.send(embed=self.bot.error(f"```py\n{traceback.format_exc()}\n```"))
			return
		await ctx.message.add_reaction("✅")

	@commands.command(hidden=True)
	@checks.is_developer()
	async def unload(self, ctx, extension):
		try:
			self.bot.unload_extension(extension)
		except Exception as e:
			await ctx.send(embed=self.bot.error(f"```py\n{traceback.format_exc()}\n```"))
			return
		await ctx.message.add_reaction("✅")

	@commands.command(hidden=True)
	@checks.is_developer()
	async def reload(self, ctx, extension):
		try:
			self.bot.unload_extension(extension)
			self.bot.load_extension(extension)
		except Exception as e:
			await ctx.send(embed=self.bot.error(f"```py\n{traceback.format_exc()}\n```"))
			return
		await ctx.message.add_reaction("✅")

	# Terminal #

	@commands.command(aliases=["terminal"], hidden=True)
	@checks.is_developer()
	async def cmd(self, ctx, *, command):

		try:
			output = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT).communicate()[0].decode("utf_8")
		except:
			await ctx.send(self.bot.error("Command execution failed"))
			return

		await ctx.send(f"```py\n{output}\n```")

	@commands.command(hidden=True)
	@checks.is_developer()
	async def pull(self, ctx):
		try:
			output = Popen("git pull", shell=True, stdout=PIPE, stderr=STDOUT).communicate()[0].decode("utf_8")
		except:
			await ctx.send(self.bot.error("Command execution failed"))
			return

		await ctx.send(f"```py\n{output}\n```")

	@commands.command(hidden=True)
	@checks.is_developer()
	async def kill(self, ctx, ):
		"""Ideally you should get an empty message back from this command"""
		try:
			output = \
			Popen(f"systemctl restart {ctx.me.name.lower()}", shell=True, stdout=PIPE, stderr=STDOUT).communicate()[
				0].decode("utf_8")
		except:
			await ctx.send(embed=self.bot.error("Restart failed"))

		await ctx.send(f"```py\n{output}\n```")

	# Database #

	@commands.command(hidden=True)
	@checks.is_developer()
	async def updatetables(self, ctx):
		statements = ["CREATE TABLE IF NOT EXISTS guild_config (guild_id BIGINT PRIMARY KEY, mod_role_id BIGINT, "
		              "admin_role_id BIGINT, greeter_role_id BIGINT)",
		              "CREATE TABLE IF NOT EXISTS statistics (id SERIAL, guild_id BIGINT, channel_id BIGINT, author_id "
		              "BIGINT, time TIMESTAMP NOT NULL DEFAULT (NOW() at time zone 'utc'), prefix TEXT, command_name TEXT)",
		              "CREATE TABLE IF NOT EXISTS log_config (guild_id BIGINT PRIMARY KEY, member_log_channel_id BIGINT, "
		              "message_log_channel_id BIGINT, invite_log_channel_id BIGINT, strike_log_channel_id BIGINT, blacklist BIGINT[], whitelist BOOL DEFAULT False)",
		              "CREATE TABLE IF NOT EXISTS event_logs (id SERIAL, action TEXT, target_id BIGINT, "
		              "user_id BIGINT, guild_id BIGINT, reason TEXT, report_message_id BIGINT, time TIMESTAMP NOT NULL DEFAULT (NOW() at time zone 'utc'))",
		              "CREATE TABLE IF NOT EXISTS message_logs (message_id BIGINT PRIMARY KEY, content TEXT, author_id "
		              "BIGINT, channel_id BIGINT, guild_id BIGINT, status TEXT, time TIMESTAMP NOT NULL DEFAULT (NOW() at time zone 'utc'))",
		              "CREATE TABLE IF NOT EXISTS word_censor (guild_id BIGINT, word TEXT, PRIMARY KEY (guild_id, word))",
		              "CREATE TABLE IF NOT EXISTS mention_censor (guild_id BIGINT PRIMARY KEY, amount INT, time INT)",
		              "CREATE TABLE IF NOT EXISTS image_censor (guild_id BIGINT PRIMARY KEY, amount INT, time INT)",
		              "CREATE TABLE IF NOT EXISTS caps (guild_id BIGINT, toggle BOOL)",
		              "CREATE TABLE IF NOT EXISTS react_roles (id SERIAL, message_id BIGINT, role_id BIGINT, emoji_id TEXT, guild_id BIGINT)",
		              "CREATE TABLE IF NOT EXISTS rift (rift_name TEXT PRIMARY KEY, owner BIGINT, channels BIGINT[], blacklist BIGINT[])",
		              "CREATE TABLE IF NOT EXISTS strike_config (guild_id BIGINT PRIMARY KEY, caps_ban INT, caps_mute INT, mention_ban INT, mention_mute INT, image_ban INT, image_mute INT, censor_ban INT, censor_mute INT)",
		              "CREATE TABLE IF NOT EXISTS strikes (user_id BIGINT, guild_id BIGINT, caps_strikes INT DEFAULT 0, mention_strikes INT DEFAULT 0, censor_strikes INT DEFAULT 0, image_strikes INT DEFAULT 0, PRIMARY KEY (guild_id, user_id))",
		              "CREATE TABLE IF NOT EXISTS weather (key TEXT)",
		              "CREATE TABLE IF NOT EXISTS welcome_config (guild_id BIGINT PRIMARY KEY, channel_id BIGINT, text_message TEXT, whisper BOOL DEFAULT False)",
		              "CREATE TABLE IF NOT EXISTS welcome_fields (id SERIAL, guild_id BIGINT, name TEXT, value Text)",
		              #"CREATE TABLE IF NOT EXISTS competition (channel_id BIGINT PRIMARY KEY, name TEXT, created TIMESTAMP NOT NULL DEFAULT (NOW() at time zone 'utc'))",
		              "CREATE TABLE IF NOT EXISTS special_roles (guild_id BIGINT, name TEXT, applied_role_id BIGINT, give_role_id BIGINT)"
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

	# Guild Management #

	@commands.command(hidden=True)
	@checks.is_developer()
	async def leave(self, ctx, id: int):
		for guild in self.bot.guilds:
			if id == guild.id:
				await guild.leave()
				await ctx.message.add_reaction("✅")
				return
		await ctx.send(embed=self.bot.error("You are not in that guild"))

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
