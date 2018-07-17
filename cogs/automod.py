from discord.ext import commands
from discord import Embed, Object
import asyncpg
from .utils import checks
from .utils import cooldown

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
		query = "SELECT * FROM word_censor"
		results = self.bot.pool.fetch(query)
		for result in results:
			if result["guild_id"] not in self.censor_cache:
				self.censor_cache[result["guild_id"]] = [result["word"]]
			else:
				self.censor_cache[result["guild_id"]].append(result["word"])

	@commands.command(aliases=["censor_add"])
	@checks.is_admin()
	async def add_censor(self, ctx, word):
		"""Add a wored to be censored. Note this looks for this word by itself and ignores if it is contained within another word. Censor will ignore case"""
		query = "INSERT into word_censor (guild_id, word) VALUES ($1, $2)"

		try:
			await self.bot.pool.execute(query, ctx.guild.id, word.lower())
			self.update_censor_cache()
		except asyncpg.UniqueViolationError:
			await ctx.send(embed=self.bot.error("This is already a censored word"))

	@commands.command(aliases=["delete_censor", "censor_delete"])
	@checks.is_admin()
	async def remove_censor(self, ctx, word):
		query = "SELECT word FROM censor WHERE (guild_id = $1) and (word = $2)"
		in_db = await self.bot.pool.fetch(query, ctx.guild.id, word.lower())

		if not in_db:
			await ctx.send(embed=self.bot.error("Not a censor word"))
			return

		query = "DELETE FROM word_censor WHERE (guild_id = $1) and (word = $2)"
		await self.bot.pool.fetch(query, ctx.guild.id, word.lower())
		await ctx.send(embed=self.bot.succes("Word removed"))
		self.update_censor_cache()


	@commands.command()
	@checks.is_admin()
	async def censor_list(self, ctx):
		query = "SELECT word FROM word_censor WHERE guild_id = $1"
		words = await self.bot.pool.fetch(query, ctx.guil.id)

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
		if await checks.has_level(proxy_ctx, "mod"):
			return

		for word in self.censor_cache[message.guild.id]:
			if f" {word} " in message.content:
				await message.delete()


	# Mention Censor

	async def update_mention_cache(self):
		query = "SELECT * FROM mention_censor"
		results = self.bot.pool.fetch(query)
		for result in results:
				self.mention_cache[result["guild_id"]] = {"amount": result["amount"], "time": result["time"]}

	async def mention_rate(self, ctx, amount: int, time: int):
		"""Set the max mention rate. For sample 3,4 would be a max of 3 mentions in a time of 4 seconds"""

		insertquery = "INSERT into word_censor (guild_id, amount, time) VALUES ($1, $2, $3)"
		updatequery = "UPDATE word_censor SET amount = $1, time = $2 WHERE guild_id = $3"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, amount, time)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(updatequery, amount, time, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f"I will allow a max of {amount} mentions in {time}s"))

		for key in list(self.mention_cache[ctx.guild.id]):  # Reset cooldowns
			if key not in ["amount", "time"]:
				self.mention_cache[ctx.guild.id].pop(key)


	async def mention_on_message(self, message):
		if not message.guild:
			return
		if message.guild.id not in self.mention_cache:
			return

		user_mentions = len(message.mentions)
		role_mentions = len(message.role_mentions)
		total_mentions = user_mentions + role_mentions

		if total_mentions < 1:
			return

		proxy_ctx = Object(id=None)
		proxy_ctx.guild = message.guild
		proxy_ctx.author = message.author
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

		number_of_caps = 0
		for letter in message.content:
			if number_of_caps >= len(message.content)/2:
				proxy_ctx = Object(id=None)
				proxy_ctx.guild = message.guild
				proxy_ctx.author = message.author
				if not await checks.has_level(proxy_ctx, "mod"):
					await message.delete()
			if letter.isupper():
				number_of_caps += 1


	# Image spam
	async def update_image_cache(self):
		query = "SELECT * FROM image_censor"
		results = self.bot.pool.fetch(query)
		for result in results:
				self.image_cache[result["guild_id"]] = {"amount": result["amount"], "time": result["time"]}

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

		if not message.attatchements:
			return

		number_of_images = len([image for image in message.attatchements if image.height])
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

