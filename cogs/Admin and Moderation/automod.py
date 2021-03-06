from discord.ext import commands
from discord import Embed, Object, Member, Forbidden
from ..utils import checks
from ..utils import cooldown
from itertools import groupby
import re
import asyncpg


class Automod:
	"""Settings to auto-moderate spam and profanity. The types are words, caps, mention, and image. Config requires admin. Mod is exempt from automod."""

	def __init__(self, bot):
		self.bot = bot
		self.category = "Admin and Moderation"
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

	# Strikes

	@commands.group(invoke_without_command=True)
	@checks.is_mod()
	@commands.guild_only()
	async def strikes(self, ctx):
		"""ADVANCED: Group of commands for muting and banning for repeat automod offences"""
		if not ctx.invoked_subcommand:
			await ctx.send(embed=self.bot.error(f"Please specify which mode you wish to use. \n{ctx.prefix}strike mode\nSee {ctx.prefix}help strikes"))

	async def strike_config(self, guild_id, _type, action, strikes):
		insertquery = f"INSERT INTO strike_config (guild_id, {_type}_{action}) VALUES ($1, $2)"
		updatequery = f"UPDATE strike_config SET {_type}_{action} = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, guild_id, strikes)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(updatequery, strikes, guild_id)

	@strikes.command()
	@checks.is_admin()
	@commands.guild_only()
	async def config(self, ctx):
		"""Strike config for the guild"""
		query = "SELECT * FROM strike_config WHERE guild_id = $1"
		config = await self.bot.pool.fetchrow(query, ctx.guild.id)
		if not config:
			await ctx.send(embed=self.bot.error("Strikes not setup on this guild"))
		else:
			caps_ban = config["caps_ban"]
			caps_mute = config["caps_mute"]
			mention_mute = config["mention_mute"]
			mention_ban = config["mention_ban"]
			image_ban = config["image_ban"]
			image_mute = config["image_mute"]
			censor_ban = config["censor_ban"]
			censor_mute = config["censor_mute"]
			embed = Embed(title=f"Strike Config for {ctx.guild.name}")
			embed.add_field(name="Caps", inline=False, value=f"Ban at: {caps_ban or 'Never'}\nMute at: {caps_mute or 'Never'}")
			embed.add_field(name="Mention", inline=False, value=f"Ban at: {mention_ban or 'Never'}\nMute at: {mention_mute or 'Never'}")
			embed.add_field(name="Image", inline=False, value=f"Ban at: {image_ban or 'Never'}\nMute at: {image_mute or 'Never'}")
			embed.add_field(name="Censor", inline=False, value=f"Ban at: {censor_ban or 'Never'}\nMute at: {censor_mute or 'Never'}")
			await ctx.send(embed=embed)

	@strikes.command()
	@checks.is_mod()
	@commands.guild_only()
	async def member(self, ctx, member: Member):
		"""Amount of strikes a certain member has"""

		query = "SELECT * FROM strikes WHERE (user_id = $1) and (guild_id = $2)"
		strikes = await self.bot.pool.fetchrow(query, member.id, ctx.guild.id)
		if not strikes:
			caps = 0
			mention = 0
			image = 0
			censor = 0
		else:
			caps = strikes["caps_strikes"]
			mention = strikes["mention_strikes"]
			image = strikes["image_strikes"]
			censor = strikes["censor_strikes"]
		embed = Embed(title=f"Strikes for {member.name}")
		embed.add_field(name="Caps", inline=False, value=caps)
		embed.add_field(name="Mention", inline=False, value=mention)
		embed.add_field(name="Image", inline=False, value=image)
		embed.add_field(name="Censor", inline=False, value=censor)
		await ctx.send(embed=embed)

	@strikes.command()
	@checks.is_admin()
	@commands.guild_only()
	async def caps(self, ctx, action, strikes: int):
		"""Set a caps threshold for action. (action can be ban or mute)"""
		action = action.lower()
		if action not in ["mute", "ban"]:
			await ctx.send(embed=self.bot.error("Not a valid action. Please select either mute or ban"))
			return

		await self.strike_config(ctx.guild.id, "caps", action, strikes)
		await ctx.send(embed=self.bot.success(f"I will now {action} on after {strikes} caps offences"))

	@strikes.command()
	@checks.is_admin()
	@commands.guild_only()
	async def mention(self, ctx, action, strikes: int):
		"""Set a mention threshold for action. (action can be ban or mute)"""
		action = action.lower()
		if action not in ["mute", "ban"]:
			await ctx.send(embed=self.bot.error("Not a valid action. Please select either mute or ban"))
			return

		await self.strike_config(ctx.guild.id, "mention", action, strikes)
		await ctx.send(embed=self.bot.success(f"I will now {action} on after {strikes} mention offences"))

	@strikes.group()
	@checks.is_admin()
	@commands.guild_only()
	async def image(self, ctx, action, strikes: int):
		"""Set an image threshold for action. (action can be ban or mute)"""
		action = action.lower()
		if action not in ["mute", "ban"]:
			await ctx.send(embed=self.bot.error("Not a valid action. Please select either mute or ban"))
			return

		await self.strike_config(ctx.guild.id, "image", action, strikes)
		await ctx.send(embed=self.bot.success(f"I will now {action} on after {strikes} image offences"))

	@strikes.group()
	@checks.is_admin()
	@commands.guild_only()
	async def censor(self, ctx, action, strikes: int):
		"""Set a censor threshold for action. (action can be ban or mute)"""
		action = action.lower()
		if action not in ["mute", "ban"]:
			await ctx.send(embed=self.bot.error("Not a valid action. Please select either mute or ban"))
			return

		await self.strike_config(ctx.guild.id, "censor", action, strikes)
		await ctx.send(embed=self.bot.success(f"I will now {action} on after {strikes} censor offences"))

	async def on_member_strike(self, member, offence, reason):
		query = f"SELECT {offence}_ban, {offence}_mute FROM strike_config WHERE guild_id = $1"
		strikes = await self.bot.pool.fetchrow(query, member.guild.id)
		if not strikes:
			return
		ban_strikes = strikes[f"{offence}_ban"]
		mute_strikes = strikes[f"{offence}_mute"]

		insertquery = f"INSERT INTO strikes (guild_id, user_id, {offence}_strikes) VALUES ($1, $2, $3)"
		updatequery = f"UPDATE strikes SET {offence}_strikes = {offence}_strikes + 1 WHERE (guild_id = $1) and (user_id = $2) RETURNING {offence}_strikes"
		try:
			await self.bot.pool.execute(insertquery, member.guild.id, member.id, 1)
			strikes = 1
		except asyncpg.UniqueViolationError:
			strikes = await self.bot.pool.fetchval(updatequery, member.guild.id, member.id)

		if ban_strikes:
			if strikes >= ban_strikes:
				try:
					await member.ban(reason=f"Triggered automod on {offence} {strikes} times")
				except Forbidden:
					return
				query = f"UPDATE strikes SET {offence}_strikes = $1 WHERE (guild_id = $2) and (user_id = $3)"
				await self.bot.pool.execute(query, 0, member.guild.id, member.id)
				return

		if mute_strikes:
			if strikes == mute_strikes:
				for tchan in member.guild.text_channels:
					reason = f"Triggered automod on {offence} {strikes} times"
					try:
						await tchan.set_permissions(member, reason=f"Triggered automod on {offence} {strikes} times",
					                                send_messages=False)
					except Forbidden:
						pass
				self.bot.dispatch("member_mute", member, reason, self.bot.user)
				if not ban_strikes:
					query = f"UPDATE strikes SET {offence}_strikes = $1 WHERE (guild_id = $2) and (user_id = $3)"
					await self.bot.pool.execute(query, 0, member.guild.id, member.id)


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

	@commands.command(aliases=["addcensor"])
	@checks.is_admin()
	@commands.guild_only()
	async def censoraddd(self, ctx, word):
		"""Add a word to be censored. Note this looks for this word by itself and ignores if it is contained within another word. Censor will ignore case"""
		query = "INSERT into word_censor (guild_id, word) VALUES ($1, $2)"

		try:
			await self.bot.pool.execute(query, ctx.guild.id, word.lower())
			await self.update_censor_cache()
			await ctx.send(embed=self.bot.success("Word added"))
		except asyncpg.UniqueViolationError:
			await ctx.send(embed=self.bot.error("This is already a censored word"))

	@commands.command(aliases=["deletecensor", "censordelete", "removecensor"])
	@checks.is_admin()
	@commands.guild_only()
	async def censorremove(self, ctx, word):
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

	@commands.command(aliases=["listcensor", "list_censor", "censor_list"])
	@checks.is_admin()
	@commands.guild_only()
	async def censorlist(self, ctx):
		"""Show all words currently censored"""
		query = "SELECT word FROM word_censor WHERE guild_id = $1"
		words = await self.bot.pool.fetch(query, ctx.guild.id)

		embed = Embed(title=f"Censor Words for {ctx.guild.name}",
		              description="\n".join([word["word"] for word in words]))

		await ctx.send(embed=embed)

	async def censor_on_message(self, message):
		if not message.guild:
			return

		if message.author.bot:
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
			try:
				await message.delete()
			except Forbidden:
				pass
			self.bot.dispatch("member_strike", message.author, "censor", message.content)

	# Mention Censor

	async def update_mention_cache(self):
		query = "SELECT * FROM mention_censor"
		results = await self.bot.pool.fetch(query)
		for result in results:
			self.mention_cache[result["guild_id"]] = {"amount": result["amount"], "time": result["time"]}

	@commands.command()
	@checks.is_admin()
	@commands.guild_only()
	async def mentionrate(self, ctx, amount: int, time: int):
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

		if message.author.bot:
			return

		if message.guild.id not in self.mention_cache:
			return

		user_mentions = len(message.raw_mentions)
		role_mentions = len(message.raw_role_mentions)
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
				try:
					await message.delete()
				except Forbidden:
					pass
				self.bot.dispatch("member_strike", message.author, "mention", message.content)

	# Caps filter

	@commands.command(aliases=["togglecaps", "capstoggle"])
	@checks.is_admin()
	@commands.guild_only()
	async def anticaps(self, ctx):
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

		if message.author.bot:
			return

		if not message.content:
			return

		number_of_caps = sum(1 for letter in message.content if letter.isupper())
		if (number_of_caps >= len(message.content)*0.6) and (len(message.content.split()) > 1):
			query = "SELECT toggle FROM caps WHERE guild_id = $1"
			caps = await self.bot.pool.fetchval(query, message.guild.id)
			if not caps:
				return
			proxy_ctx = Object(id=None)
			proxy_ctx.guild = message.guild
			proxy_ctx.author = message.author
			proxy_ctx.bot = self.bot
			if not await checks.has_level(proxy_ctx, "mod"):
				try:
					await message.delete()
				except Forbidden:
					pass
				self.bot.dispatch("member_strike", message.author, "caps", message.content)

	# Image spam
	async def update_image_cache(self):
		query = "SELECT * FROM image_censor"
		results = await self.bot.pool.fetch(query)
		for result in results:
			self.image_cache[result["guild_id"]] = {"amount": result["amount"], "time": result["time"]}

	@commands.command()
	@checks.is_admin()
	@commands.guild_only()
	async def imagerate(self, ctx, amount: int, time: int):
		"""Set the max image rate. For sample 3,4 would be a max of 3 images in a time of 4 seconds"""

		insertquery = "INSERT into image_censor (guild_id, amount, time) VALUES ($1, $2, $3)"
		updatequery = "UPDATE image_censor SET amount = $1, time = $2 WHERE guild_id = $3"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, amount, time)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(updatequery, amount, time, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f"I will allow a max of {amount} images in {time}s"))

		if ctx.guild.id in self.image_cache:
			for key in list(self.image_cache[ctx.guild.id]):  # Reset cooldowns
				if key not in ["amount", "time"]:
					self.image_cache[ctx.guild.id].pop(key)

		await self.update_image_cache()

	async def image_on_message(self, message):
		if not message.guild:
			return

		if message.author.bot:
			return

		if not message.attachments:
			return

		number_of_images = sum([1 for image in message.attachments if image.height])
		if number_of_images < 1:
			return

		if message.guild.id not in self.image_cache:
			return

		proxy_ctx = Object(id=None)
		proxy_ctx.guild = message.guild
		proxy_ctx.author = message.author
		proxy_ctx.bot = self.bot
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
				try:
					await message.delete()
				except Forbidden:
					pass
				self.bot.dispatch("member_strike", message.author, "image",
				                  "\n".join(attachment.url for attachment in message.attachments))


def setup(bot):
	cog = Automod(bot)
	bot.add_cog(cog)
	bot.add_listener(cog.censor_on_message, "on_message")
	bot.add_listener(cog.mention_on_message, "on_message")
	bot.add_listener(cog.image_on_message, "on_message")
	bot.add_listener(cog.caps_on_message, "on_message")
