from discord.ext import commands
from discord import Embed, Object
import asyncpg
from .utils import checks
from .utils import cooldown
from itertools import groupby
import re


class Automod:

	def __init__(self, bot):
		self.bot = bot
		self.censor_cache = {}
		self.censor_task = self.bot.loop.create_task(self.update_censor_cache())
		self.mention_cache = {}
		self.mention_task = self.bot.loop.create_task(self.update_mention_cache())
		self.image_cache = {}
		self.image_task = self.bot.loop.create_task(self.update_image_cache())

	def __unload(self):
		self.censor_task.cancel()
		self.mention_task.cancel()
		self.image_task.cancel()

	# Censor

	async def update_censor_cache(self):
		""" Set a class attribute containing the regexes per guild

		Looks something like this
		{
			372581201195565056: re.compile('\\b(clown)|(pleb)\\b'),
			472348120139456505: re.compile('\\b(fool)|(idiot)\\b')
		}

		"""
		query = "SELECT * FROM word_censor"
		results = await self.bot.pool.fetch(query)
		results.sort(key=lambda result: result["guild_id"])
		for k, v in groupby(results, key=lambda result: result["guild_id"]):
			self.censor_cache[k] = re.compile("\\b"+"|".join([f"({result['word']})" for result in list(v)])+"\\b")

	@commands.command(aliases=["censor_add"])
	@checks.is_admin()
	async def add_censor(self, ctx, word):
		"""Add a word to be censored. Note this looks for this word by itself and ignores if it is contained within another word. Censor will ignore case"""
		query = "INSERT into word_censor (guild_id, word) VALUES ($1, $2)"

		try:
			await self.bot.pool.execute(query, ctx.guild.id, word.lower())
			await self.update_censor_cache()
			await ctx.send(embed=self.bot.success("Word added"))
		except asyncpg.UniqueViolationError:
			await ctx.send(embed=self.bot.error("This is already a censored word"))

	@commands.command(aliases=["delete_censor", "censor_delete"])
	@checks.is_admin()
	async def remove_censor(self, ctx, word):
		"""Remove a word from being censored"""
		query = "SELECT word FROM word_censor WHERE (guild_id = $1) and (word = $2)"
		in_db = await self.bot.pool.fetch(query, ctx.guild.id, word.lower())

		if not in_db:
			await ctx.send(embed=self.bot.error("Not a censor word"))
			return

		query = "DELETE FROM word_censor WHERE (guild_id = $1) and (word = $2)"
		await self.bot.pool.fetch(query, ctx.guild.id, word.lower())
		await self.update_censor_cache()
		await ctx.send(embed=self.bot.success("Word removed"))

	@commands.command()
	@checks.is_admin()
	async def censor_list(self, ctx):
		"""Show all words currently censored"""
		query = "SELECT word FROM word_censor WHERE guild_id = $1"
		words = await self.bot.pool.fetch(query, ctx.guild.id)

		embed = Embed(title=f"Censor Words for {ctx.guild.name}",
		              description="\n".join([word["word"] for word in words]))

		await ctx.send(embed=embed)

	async def censor_on_message(self, message):
		if not message.guild:
			return
		if message.guild.id not in self.censor_cache:
			return

		proxy_ctx = Object(id=None)
		proxy_ctx.guild = message.guild
		proxy_ctx.author = message.author
		proxy_ctx.bot = self.bot
		if await checks.has_level(proxy_ctx, "mod"):
			return

		if self.censor_cache[message.guild.id].search(message.content):
			await message.delete()

	# Mention Censor

	async def update_mention_cache(self):
		query = "SELECT * FROM mention_censor"
		results = await self.bot.pool.fetch(query)
		for result in results:
			self.mention_cache[result["guild_id"]] = {"amount": result["amount"], "time": result["time"]}

	@commands.command()
	async def mention_rate(self, ctx, amount: int, time: int):
		"""Set the max mention rate. For sample 3,4 would be a max of 3 mentions in a time of 4 seconds"""

		insertquery = "INSERT into mention_censor (guild_id, amount, time) VALUES ($1, $2, $3)"
		updatequery = "UPDATE mention_censor SET amount = $1, time = $2 WHERE guild_id = $3"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, amount, time)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(updatequery, amount, time, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f"I will allow a max of {amount} mentions in {time}s"))

		if ctx.guild.id in self.mention_cache:
			for key in list(self.mention_cache[ctx.guild.id]):  # Reset cooldowns
				if key not in ["amount", "time"]:
					self.mention_cache[ctx.guild.id].pop(key)

		await self.update_mention_cache()

	async def mention_on_message(self, message):
		if not message.guild:
			return
		if message.guild.id not in self.mention_cache:
			return

		user_mentions = len(message.mentions)
		role_mentions = len(message.role_mentions)
		total_mentions = user_mentions+role_mentions

		if total_mentions < 1:
			return

		proxy_ctx = Object(id=None)
		proxy_ctx.guild = message.guild
		proxy_ctx.author = message.author
		proxy_ctx.bot = self.bot
		if await checks.has_level(proxy_ctx, "mod"):
			return

		if message.author not in self.mention_cache[message.guild.id]:
			amount = self.mention_cache[message.guild.id]["amount"]
			time = self.mention_cache[message.guild.id]["time"]
			self.mention_cache[message.guild.id][message.author] = cooldown.Cooldown(amount, time)

		user_cooldown = self.mention_cache[message.guild.id][message.author]
		user_cooldown.check_reset()

		for mention in range(0, total_mentions):
			user_cooldown.increment()
			if user_cooldown.is_allowed():
				pass
			else:
				await message.delete()

	# Caps filter

	@commands.command()
	async def toggle_anticaps(self, ctx):
		"""Toggles whether to delete messages with over 50% of the message in caps"""

		insertquery = "INSERT INTO caps (guild_id, toggle) VALUES ($1, $2) RETURNING toggle"
		updatequery = "UPDATE caps SET toggle = NOT toggle WHERE guild_id = $1 RETURNING toggle"

		try:
			caps = await self.bot.pool.fetchval(insertquery, ctx.guild.id, True)
		except asyncpg.UniqueViolationError:
			caps = await self.bot.pool.fetchval(updatequery, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f"Anticaps set to {caps}"))

	async def caps_on_message(self, message):
		if not message.guild:
			return

		number_of_caps = sum(1 for letter in message.content if letter.isupper())
		if number_of_caps >= len(message.content)/2:
			proxy_ctx = Object(id=None)
			proxy_ctx.guild = message.guild
			proxy_ctx.author = message.author
			proxy_ctx.bot = self.bot
			if not await checks.has_level(proxy_ctx, "mod"):
				await message.delete()


	# Image spam
	async def update_image_cache(self):
		query = "SELECT * FROM image_censor"
		results = self.bot.pool.fetch(query)
		for result in results:
			self.image_cache[result["guild_id"]] = {"amount": result["amount"], "time": result["time"]}

	@commands.command()
	async def image_rate(self, ctx, amount: int, time: int):
		"""Set the max image rate. For sample 3,4 would be a max of 3 images in a time of 4 seconds"""

		insertquery = "INSERT into image_censor (guild_id, amount, time) VALUES ($1, $2, $3)"
		updatequery = "UPDATE image_censor SET amount = $1, time = $2 WHERE guild_id = $3"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, amount, time)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(updatequery, amount, time, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f"I will allow a max of {amount} images in {time}s"))

		for key in list(self.image_cache[ctx.guild.id]):  # Reset cooldowns
			if key not in ["amount", "time"]:
				self.image_cache[ctx.guild.id].pop(key)

	async def image_on_message(self, message):
		if not message.guild:
			return

		if not message.attachments:
			return

		number_of_images = len([image for image in message.attachments if image.height])
		if number_of_images < 1:
			return

		if message.guild.id not in self.image_cache:
			return

		proxy_ctx = Object(id=None)
		proxy_ctx.guild = message.guild
		proxy_ctx.author = message.author
		if await checks.has_level(proxy_ctx, "mod"):
			return

		if message.author not in self.image_cache[message.guild.id]:
			amount = self.image_cache[message.guild.id]["amount"]
			time = self.image_cache[message.guild.id]["time"]
			self.image_cache[message.guild.id][message.author] = cooldown.Cooldown(amount, time)

		user_cooldown = self.image_cache[message.guild.id][message.author]
		user_cooldown.check_reset()

		for mention in range(0, number_of_images):
			user_cooldown.increment()
			if user_cooldown.is_allowed():
				pass
			else:
				await message.delete()


def setup(bot):
	cog = Automod(bot)
	bot.add_cog(cog)
	bot.add_listener(cog.censor_on_message, "on_message")
	bot.add_listener(cog.mention_on_message, "on_message")
	bot.add_listener(cog.image_on_message, "on_message")
	bot.add_listener(cog.caps_on_message, "on_message")
