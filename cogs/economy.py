
import discord
from discord.ext import commands
import asyncpg

from .utils import checks

def bankmanagerembed(message):
	embed = discord.Embed(description=message)
	embed.set_author(name="The bank manager of YoirBank says...", icon_url="https://cdn.discordapp.com/avatars/378073671014809612/454d95735bd20bad792ae45a58777a37.webp?size=1024")
	return embed

def shopmanagerembed(message):
	embed = discord.Embed(description=message)
	embed.set_author(name="The shop clerk at YoriShop says...", icon_url="https://cdn.discordapp.com/avatars/378073671014809612/454d95735bd20bad792ae45a58777a37.webp?size=1024")
	return embed


#create table economy_config (guild_id BIGINT unique, drop_rate INT, drop_amount_min INT, drop_amount_max INT, channels BIGINT[], currency TEXT)
class Economy():
	"""Commands related to bank accounts"""
	def __init__(self, bot):
		self.bot = bot

	#Utility functions
	async def getbalance(self, user_id, guild_id):
		query = "SELECT balance FROM bank WHERE user_id = $1 AND guild_id = 2"
		balance = await self.bot.pool.fetchval(query, user_id, guild_only)
		return balance or 0

	#Note change_amount can be negative here
	async def changebalance(self, user_id, guild_id, change_amount):
		query = "UPDATE bank SET balance = balance + $3 WHERE user_id = $1 and guild_id = $2"
		alterquery = "INSERT INTO bank (user_id, guild_id, balance) VALUES ($1,$2,$3)"

		await self.bot.pool.execute(query, user_id, guild_id, change_amount)

	async def setbalance(self, user_id, guild_id, new_balance):
		query = "UPDATE bank SET balance = $1 WHERE user_id = $2 and guild_id = $3"
		alterquery = "INSERT INTO bank (user_id, guild_id, balance) VALUES ($1,$2,$3)"

		await self.bot.pool.execute(query, user_id, guild_id, new_balance)


	
	#Commands

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def economyconfig(self, ctx):
		"""Show all Economy setting for your guild"""

		query = "SELECT * FROM economy_config WHERE guild_id = $1"
		results = await ctx.db.fetchrow(query, ctx.guild.id)

		if not results:
			await ctx.send(embed=self.bot.error("No Economy settings set"))
			return

		embed = discord.Embed(title="Settings for {}".format(ctx.guild.name))
		
		drop_channels = ""
		for channel_id in drop_channels:
			channel = self.bot.get_channel(channel_id)
			drop_channels + channel.mention if channel else "Deleted" + "\n"

		embed.add_field(name="Drop channels", value=drop_channels or "None", inline=False)
		embed.add_field(name="Drop Rate", value=results["drop_rate"], inline=False)
		embed.add_field(name="Minimum Drop", value=results["drop_amount_min"], inline=False)
		embed.add_field(name="Maximum Drop", value=results["drop_amount_max"], inline=False)
		embed.add_field(name="Currency", value=results["currency"], inline=False)

		await ctx.send(embed=embed)





	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def adddropchannel(self, ctx, channel: discord.TextChannel):
		"""Add a channel to the list of channels that drops can happen"""

		query = "SELECT * FROM economy_config WHERE guild_id = $1"
		results = await ctx.db.fetchrow(query, ctx.guild.id)

		if not results:
			query = "INSERT INTO economy_config (channels) VALUES $1"
			await ctx.db.execute(query, [channel.id])
			await ctx.send(embed=self.bot.success("Channel added"))

		if results["channels"]:
			channels = results["channels"]
			channels.append(channel.id)
		else:
			channels = [channel.id]

		query = "UPDATE economy_config SET channels = $1 WHERE guild_id = $2"
		await ctx.db.execute(query, channels, ctx.guild.id)
		await ctx.send(embed=self.bot.success("Channel Added"))



	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def removeropchannel(self, ctx, channel: discord.TextChannel):
		"""Delete a channel to the list of channels that drops can happen"""

		query = "SELECT * FROM economy_config WHERE guild_id = $1"
		results = await ctx.db.fetchrow(query, ctx.guild.id)

		if not results:
			await ctx.send(embed=self.bot.error("You don't have any channels"))
			return
		if not results["channels"]:
			await ctx.send(embed=self.bot.error("You don't have any channels"))
			return
		if channel.id not in results["channels"]:
			await ctx.send(embed=self.bot.error("This is not a drop channel"))
			return

		channels = results["channels"]
		channels.remove(channe.id)
		await ctx.send(embed=self.bot.success("Channel removed"))

	#Admin section of commands
	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def setdroprate(self, ctx, drop_rate : int):
		"""Sets the rate at which the bot will randomly drop random amounts of currency. 0 for no drops. Default is 0. Drop counter begins after collection"""
		if drop_rate < 600:
			await ctx.send(embed=bankmanagerembed("I can't just be dropping currency like that please request a time greater than 600 seconds."))
			return

		insertquery = "INSERT INTO economy_config (guild_id, drop_rate) VALUES ($1, $2)"
		updatequery = "UPDATE economy_config SET per_second = $1 WHERE guild_id = $2"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, drop_rate)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(updatequery, drop_rate, ctx.guild.id)

		await ctx.send(embed=bankmanagerembed("I will drop currency every {} seconds".format(drop_rate))) 

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def setdropamounts(self, ctx, min : int, max : int):
		"""Sets the minimum and maximum for random drops. Min default = 10, Max default = 20"""

		if min < 1:
			await ctx.send(embed=bankmanagerembed("I can't drop currency less than 1"))
			return
		if max <= min:
			await ctx.send(embed=bankmanagerembed("The minimum amount must be less than the maximum amount"))
			return

		insertquery = "INSERT INTO economy_config (guild_id, drop_amount_min, drop_amount_max) VALUES ($1, $2, $3)"
		updatequery = "UPDATE economy_config SET drop_amount_min = $1, drop_amount_max = $2 WHERE guild_id = $3"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, min, max)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(updatequery, min, max, ctx.guild.id)

		if max > 100000:
			await ctx.send(embed=bankmanagerembed("I will attempt to drop a random amount of currency between {} amd {} but {} is a large amount so don't blame me if someone's bank breaks".format(min, max, max)))
		else:
			await ctx.send(embed=bankmanagerembed("I will drop a random amount of currency between {} and {}".format(min, max))) 



	
	@commands.command()
	@commands.guild_only()	
	@checks.is_admin()
	async def setcurrency(self, ctx, currency : str):
		"""Sets the characters for the currency. It is reccomended one emoji is used however the bot will support any mix of characters up to 100 characters"""

		if len(currency) >= 100:
			await ctx.send(embed=bankmanagerembed("That is too many characters for me to handle. Please send less than 100"))
			return

		insertquery = "INSERT INTO economy_config (guild_id, currency) VALUES ($1, $2)"
		updatequery = "UPDATE economy_config SET currency = $1 WHERE guild_id = $2"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, currency)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(updatequery, currency, currency)

		await ctx.send(embed=bankmanagerembed("I have set your currency to {}".format(currency)))



	@commands.command()
	@commands.guild_only()	
	@checks.is_admin()
	async def clearbanks(self, ctx):
		"""Clears the banks of every member of the guild"""

		await ctx.send("This will reset the banks for everyone in this server. Are you sure you want to do this? (yes/no)")

		def check(m):
			try:
				if m.author != ctx.message.author:
					return False
				if m.channel != ctx.message.channel:
					return False
				return True
			except:
				return False

		choice = await self.bot.wait_for('message', check=check, timeout=30.0)

		if choice.content in ["yes","Yes"]:
			#empty banks
			await ctx.send(embed=bankmanagerembed("I have emptied everyone's bank account"))
		else:
			await ctx.send(embed=bankmanagerembed("I will not empty everyone's bank account"))

	#User section of commands
	@commands.command()
	@commands.guild_only()
	async def balance(self, ctx):
		"""Retrieves your bank balance"""
		guild = ctx.guild
		author = ctx.author
		author_balance = await self.getbalance(author.id, guild.id)
		guild_currency = await self.getcurrency(guild.id)
		await ctx.send(embed=bankmanagerembed("Your balance is {} {}".format(author_balance, guild_currency)))

	@commands.command()
	@commands.guild_only()
	async def pay(self, ctx, user: discord.Member, amount: int):
		"""Pays another member out of your bank"""
		guild = ctx.guild
		author = ctx.author
		author_balance = await self.getbalance(author.id, guild.id)
		guild_currency = await self.getcurrency(guild.id)

		if author_balance < amount:
			await ctx.send(embed=bankmanagerembed("Your balance is only {} {}".format(author_balance, guild_currency)))

	@commands.command()
	@commands.guild_only()
	async def richlist(self, ctx, number=10):
		"""Shows the top rich people in the guild"""
		pass



class Shop():
	"""Shop related commands"""

	def __init__(bot, economy):
		self.bot = bot
		self.economy = economy

	
	#Admin related commands
	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def additem(self, ctx, item_name, item_value, quantity=None):
		"""Adds an item to a shop. Quantity defaults to unlimted. Items will say out of stock until removed"""
		pass

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def removeitem(self, ctx, item_name, quantity=None):
		"""Removes an item from the shop. Quantity defaults to all. If item is left in the out of stock list then it will appear in owned items"""
		pass

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def addroleitem(self, ctx, role : discord.Role, item_value, quantity=None):
		"""Adds a role item to a shop. Quantity defaults to unlimted. Items will say out of stock until removed"""
		pass

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def removeroleitem(self, ctx, role : discord.Role, quantity=None):
		"""Remove a role item to a shop. Quantity defaults to all. If item is left in the out of stock list then it will appear in owned items"""
		pass

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def interactiveshop(self, ctx):
		"""Shows the interactive version of the shop. Users can buy items with emoji reactions"""
		pass

	#User shop commands
	@commands.command()
	@commands.guild_only()
	async def buy(self, ctx, item):
		"""Buys an item from the shop"""
		pass

	@commands.command()
	@commands.guild_only()
	async def sell(self, ctx, item, person_buying : discord.Member):
		"""Sells an item to another member. They must accept the transaction"""
		pass

	@commands.command()
	@commands.guild_only()
	async def owneditems(self, ctx):
		"""Shows all of the items you own."""
		pass


def setup(bot):
	cog = Economy(bot)
	bot.add_cog(cog)
