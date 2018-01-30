

def bankmanagerembed(message):
	embed = discord.Embed(description=message)
	em.set_author(name="The bank manager of YoirBank says...", icon_url=ctx.me.avatar_url)
	return embed

def shopmanagerembed(message):
	embed = discord.Embed(description=message)
	em.set_author(name="The shop clerk at YoriShop says...", icon_url=ctx.me.avatar_url)
	return embed


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
		query = "UPDATE bank SET balance = balance + 1 WHERE user_id = $1 and guild_id = $2"
		alterquery = "INSERT INTO bank (user_id, guild_id, balance) VALUES ($1,$2,$3)"

		await self.bot.pool.execute(query, user_id, guild_id, change_amount)

	async def setbalance(self, user_id, guild_id, new_balance):
		query = "UPDATE bank SET balance = $1 WHERE user_id = $2 and guild_id = $3"
		alterquery = "INSERT INTO bank (user_id, guild_id, balance) VALUES ($1,$2,$3)"

		await self.bot.pool.execute(query, user_id, guild_id, new_balance)


	#Admin section of commands
	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def setdroprate(self, ctx, drop_rate : int):
		"""Sets the rate at which the bot will randomly drop random amounts of currency. Minimum is 600 seconds and must be in 10 minute intervals. 0 for no drops. Default is 0"""
		if drop_rate < 600:
			await ctx.send(embed=bankmanagerembed("I can't just be dropping currency like that please request a time greater than 600 seconds."))
			return

		if drop_rate % 60 != 0:
			round_down_time = drop_rate - drop_rate % 60
			await ctx.send(embed=bankmanagerembed("I do my dropping currecny round every 10 minutes. Try asking me again with {}".format(round_down_time)))
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
		if max >= min:
			await ctx.send(embed=bankmanagerembed("The minimum amount must be less than the maximum amount"))

		insertquery = "INSERT INTO economy_config (guild_id, drop_amount_min, drop_amount_max) VALUES ($1, $2, $3)"
		updatequery = "UPDATE economy_config SET drop_amount_min = $1, drop_amount_max = $2 WHERE guild_id = $2"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, per_second)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(updatequery, per_second, ctx.guild.id)

		if max > 10000:
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
		updatequery = "UPDATE bank SET currency = $1 WHERE guild_id = $2"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, currency)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(updatequery, per_second, currency)

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

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def removeitem(self, ctx, item_name, quantity=None):
		"""Removes an item from the shop. Quantity defaults to all. If item is left in the out of stock list then it will appear in owned items"""

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def addroleitem(self, ctx, role = discord.Role, item_value, quantity=None):
		"""Adds a role item to a shop. Quantity defaults to unlimted. Items will say out of stock until removed"""

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def removeroleitem(self, ctx, role = discord.Role, quantity=None):
		"""Remove a role item to a shop. Quantity defaults to all. If item is left in the out of stock list then it will appear in owned items"""

	@commands.command()
	@commands.guild_only()
	@check.is_admin()
	async def interactiveshop(self, ctx):
		"""Shows the interactive version of the shop. Users can buy items with emoji reactions"""

	#User shop commands
	@commands.command()
	@commands.guild_only()
	async def buy(self, ctx, item):
	"""Buys an item from the shop"""

	@commands.command()
	@commands.guild_only()
	async def sell(self, ctx, item, person_buying : discord.Member):
	"""Sells an item to another member. They must accept the transaction"""

	@commands.command()
	@commands.guild_only()
	async def owneditems(self, ctx):
	"""Shows all of the items you own."""

	async def on_reaction_add(reaction):















		
