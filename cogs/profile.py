from .utils import db, checks, formats, cache
from .utils.paginator import Pages
from .utils.dataIO import dataIO
from discord.ext import commands
from .utils.formats import TabularData, Plural
import json
import re
import datetime
import discord
import asyncio
import traceback
import asyncpg
import psutil
import os

class Rank:

	def __init__(self, bot : commands.Bot):
		self.bot = bot
		self.loaded_settings = False
		self.message_data = dataIO.load_json("data/rank/message_data.json")
		self.ranks = None

	def save_message_data(self):
		dataIO.save_json("data/rank/message_data.json", self.message_data)

	async def check_level(self, member, guild, message):
		xp = self.message_data[str(member.id)][str(guild.id)]
		for rank in self.ranks:
			if rank["guild_id"] == guild.id and rank["xp_required"] == xp:
				role = discord.utils.get(guild.roles, id=rank["role_id"])
				await member.add_roles(role)
				await message.channel.send("Congratualtions {} you now have the rank of {}".format(member.name, role.name))
	
	async def load_settings(self):
		self.ranks = await self.bot.pool.fetch("SELECT * FROM rank")
		if not self.ranks:
			self.ranks = []
		if not self.message_data:
			self.message_data = {}
		self.loaded_settings = True
	
	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def addrank(self, ctx, rank_role : discord.Role, xp_required : int):
		"""Will add the given rank to the rank system at the given xp_required"""
		if not self.loaded_settings:
			await self.load_settings()
		query = "INSERT INTO rank (guild_id, role_id, xp_required) VALUES ($1, $2, $3)"
		await ctx.db.execute(query, ctx.guild.id, rank_role.id, xp_required)
		self.ranks = await ctx.db.fetch("SELECT * FROM rank")
		await ctx.send("Rank added")

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def removerank(self, ctx, rank_role: discord.Role):
		"""Will remove the given rank from the rank system"""
		if not self.load_settings:
			await self.load_settings()
		query = "DELETE FROM rank WHERE guild_id = $1 and role_id = $2"
		await ctx.db.execute(query, ctx.guild.id, rank_role.id)

	@commands.command()
	@commands.guild_only()
	async def listranks(self, ctx):
		"""Will remove the given rank from the rank system"""
		if not self.load_settings:
			await self.load_settings()

		query = "SELECT * FROM rank WHERE guild_id = $1"
		ranks = await ctx.db.fetch(query, ctx.guild.id)
		text = "**The following are available for you to earn**:\n\n"
		headers = ["Role", "XP Required"]
		table = TabularData()
		table.set_columns(headers)
		humanranks = []
		for rank in ranks:
			role = discord.utils.get(ctx.guild.roles, id=rank["role_id"])
			if role:
				humanranks.append([role.mention, rank["xp_required"]])
			else:
				humanranks.append(["@deleted_role"],["xp_required"])
		table.add_rows(humanranks)
		render = table.render()
		text += render
		em = discord.Embed(color=ctx.message.author.color, description=text)
		em.set_author(name="Ranks", icon_url="http://bit.ly/2rnwE4T")
		await ctx.send(embed=em)


	async def on_message(self, ctx):
		member = ctx.author
		guild = ctx.guild

		if not self.loaded_settings:
			await self.load_settings()

		if str(member.id) in self.message_data:
			if str(guild.id) in self.message_data[str(member.id)]:
				self.message_data[str(member.id)][str(guild.id)] += 1
			else:
				self.message_data[str(member.id)][str(guild.id)] = 1
			self.message_data[str(member.id)]["global"] += 1
		else:
			self.message_data[str(member.id)] = {str(guild.id) : 1, "global" : 1}

		await self.check_level(member, guild, ctx)



	@commands.command()
	@commands.guild_only()
	async def xp(self, ctx):
		if not self.loaded_settings:
			await self.load_settings()

		if str(ctx.author.id) in self.message_data:
			await ctx.send(self.message_data[str(ctx.author.id)][str(ctx.guild.id)])
		else:
			await ctx.send("0")

	@commands.command()
	@commands.guild_only()
	async def globalxp(self, ctx):
		if not self.loaded_settings:
			await self.load_settings()

		if str(ctx.author.id) in self.message_data:
			await ctx.send(self.message_data[str(ctx.author.id)]["global"])
		else:
			await ctx.send("0")

class Profile:
	"""Commands used to set up your server profile"""

	def __init__(self, bot: commands.Bot):
		self.bot = bot
	
	@commands.command()
	async def profilehelp(self, ctx):
		"""Sends help information on how to use the profile features."""
		prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]
		em = discord.Embed(color=ctx.message.author.color, description="Need help setting up your profile? No worries, here are some pointers:")
		em.set_author(name="Profile Setup Help", icon_url="http://yoribot.com/wp-content/uploads/2017/11/yoriicon.png")
		em.add_field(name='Adding Your Region', value='Use one of the following commands:\n\n``' + prefix + 'northamerica`` `` ' + prefix + 'southamerica`` `` ' + prefix + 'europe`` `` ' + prefix + 'africa`` `` ' + prefix + 'asia`` `` ' + prefix + 'oceania``\n', inline=False)
		em.add_field(name='Adding Gender', value='Use `` ' + prefix + 'gender <gender>`` for example:\n\n``' + prefix + 'gender Male`` **or** `` ' + prefix + 'gender Female`` **or** `` ' + prefix + 'gender intersex``\n', inline=False)
		em.add_field(name='Adding Sexuality', value='Use `` ' + prefix + 'sexuality <sexuality>`` for example:\n\n``' + prefix + 'sexuality Straight`` **or** ``' + prefix + 'sexuality Gay`` **or** ``' + prefix + 'sexuality Lesbian`` **or**\n``' + prefix + 'sexuality Asexual``', inline=False)
		em.add_field(name='Adding Age', value='Use `` ' + prefix + 'age <age>`` for example:\n\n``' + prefix + 'age 20``', inline=False)
		em.add_field(name='Custom Fields', value='You can add custom sections to your profile using \n\n`` ' + prefix + 'profileadd``\n'
					'\nThe bot will then prompt you for a section title and content. P.S. You have 5 mins to do this.\n', inline=False)
		em.set_footer(text= "Use the help command or visit http://yoribot.com for more information.")
		await ctx.send(embed=em)
	
	def get_bot_uptime(self, *, brief=False):
		now = datetime.datetime.utcnow()
		delta = now - self.bot.uptime
		hours, remainder = divmod(int(delta.total_seconds()), 3600)
		minutes, seconds = divmod(remainder, 60)
		days, hours = divmod(hours, 24)

		if not brief:
			if days:
				 fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
			else:
				fmt = '{h} hours, {m} minutes, and {s} seconds'
		else:
			fmt = '{h}h {m}m {s}s'
			if days:
				fmt = '{d}d ' + fmt

		return fmt.format(d=days, h=hours, m=minutes, s=seconds)

	async def sendYori(self, ctx):

		total_members = sum(1 for _ in self.bot.get_all_members())
		total_online = len({m.id for m in self.bot.get_all_members() if m.status is discord.Status.online})
		total_unique = len(self.bot.users)
		voice_channels = []
		text_channels = []
		for guild in self.bot.guilds:
			voice_channels.extend(guild.voice_channels)
			text_channels.extend(guild.text_channels)

		text = len(text_channels)
		voice = len(voice_channels)
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name=ctx.bot.user.name, icon_url=ctx.message.guild.icon_url)
		embed.set_thumbnail(url=ctx.bot.user.avatar_url)
		embed.add_field(name='Age', value= "Old Enough")
		embed.add_field(name='Region', value="Anywhere and Everywhere")
		embed.add_field(name='Gender', value="Agender")
		embed.add_field(name='Sexuality', value="Asexual")
		embed.add_field(name='About Me', value="I am a one of the best Discord bots around - I am easy to use and I have a ton of fun features :grin:")
		embed.add_field(name='Members', value=f'{total_members} total\n{total_unique} unique\n{total_online} unique online')
		embed.add_field(name='Channels', value=f'{text + voice} total\n{text} text\n{voice} voice')
		process = psutil.Process()
		memory_usage = process.memory_full_info().uss / 1024**2
		cpu_usage = process.cpu_percent() / psutil.cpu_count()
		embed.add_field(name='Process', value=f'{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU')
		embed.add_field(name='Guilds Playing Music', value=len(self.bot.voice_clients))
		embed.add_field(name='Guilds', value=len(self.bot.guilds))
		embed.add_field(name='Commands Run', value=sum(self.bot.command_stats.values()))
		embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))
		embed.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')
		await ctx.send(embed=embed)

	@commands.command()
	@commands.guild_only()
	async def profile(self, ctx, user: discord.Member=None):
		"""Displays the profile of a mentioned user or the caller if no mention is provided"""

		if user == ctx.bot.user:
			await self.sendYori(ctx)
			return
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		query = "SELECT * FROM profile WHERE user_id = $1;"
		if user is None:
			profile = await ctx.db.fetch(query, ctx.author.id)
			embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.guild.icon_url)
			embed.set_thumbnail(url=ctx.message.author.avatar_url)
		else:
			profile = await ctx.db.fetch(query, user.id)
			embed.set_author(name=user.name, icon_url=ctx.message.guild.icon_url)
			embed.set_thumbnail(url=user.avatar_url)

		if not profile:
			await ctx.send("This person has not made a profile yet")
			return



		embed.add_field(name='Age', value= profile[0]['age'] or "Not Provided")
		embed.add_field(name='Region', value= profile[0]['region'] or "Not Provided")
		embed.add_field(name='Gender', value= profile[0]['gender'] or "Not Provided")
		embed.add_field(name='Sexuality', value= profile[0]['sexuality'] or "Not Provided")

		if profile[0]['fields']:
			for fields in profile[0]['fields']:
				if fields[0] =="image":
					embed.set_image(url=fields[1])
				else:
					embed.add_field(name=fields[0], value=fields[1].format(ctx.message.author))


		await ctx.send(embed=embed)

	@commands.command()
	@commands.guild_only()
	async def profileadd(self, ctx, name=None, *, value=None):
		"""Use the command by itself for the bot to prompt you for the title and content or enter both after the command."""

		def check(m):
			if m.author != ctx.message.author:
				return False
			if m.channel != ctx.message.channel:
				return False
			return True

		
		if (name is None):
			await ctx.send("What would you like the title to be?")
			name = await self.bot.wait_for('message', timeout=300.0, check=check)
			name = name.content
			while len(name) > 256:
				await ctx.send("Field names must be 256 characters or shorter. Re-type the content")
				name = await self.bot.wait_for('message', timeout=300.0, check=check)#
				name = name.content
		if (value is None):
			await ctx.send("What would you like the content to be?")
			value = await self.bot.wait_for('message', timeout=300.0, check=check)
			value = value.content
			while len(value) > 1024:
				await ctx.send("Field content must be 1024 characters or shorter. Re-type the content")
				value = await self.bot.wait_for('message', timeout=300.0, check=check)
				value = value.content

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			fields = [[name,value]]
			query = "INSERT INTO Profile (guild_id, user_id, fields) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, fields)
			await ctx.send("Field Added")
		elif not results[0]['fields']:
			fields = [[name,value]]
			query = "UPDATE Profile SET fields = $1 WHERE user_id = $2"
			await ctx.db.execute(query, fields, ctx.message.author.id)
			await ctx.send("Field added")
		else:
			fields = results[0]['fields']
			fields.append([name,value])
			query = "UPDATE Profile SET fields = $1 WHERE user_id = $2"
			await ctx.db.execute(query, fields, ctx.message.author.id)
			await ctx.send("Field added")

	@commands.command()
	@commands.guild_only()
	async def age(self, ctx, age: int):
		"""Sets the age of the caller"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, age) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, age)
			await ctx.send("Age Set")
		else:
			query = "UPDATE Profile SET age = $1 WHERE user_id = $2"
			await ctx.db.execute(query, age, ctx.message.author.id)
			await ctx.send("Age Set")

	@commands.command()
	@commands.guild_only()
	async def gender(self, ctx, *, gender):
		"""Sets the gender of the caller"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, gender) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, gender)
			await ctx.send("Gender Set")
		else:
			query = "UPDATE Profile SET gender = $1 WHERE user_id = $2"
			await ctx.db.execute(query, gender, ctx.message.author.id)
			await ctx.send("Gender Set")

	@commands.command()
	@commands.guild_only()
	async def sexuality(self, ctx, *, sexuality):
		"""Sets the sexuality of the caller"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, sexuality) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, sexuality)
			await ctx.send("Sexuality Set")
		else:
			query = "UPDATE Profile SET sexuality = $1 WHERE user_id = $2"
			await ctx.db.execute(query, sexuality, ctx.message.author.id)
			await ctx.send("Sexuality Set")

	@commands.command(aliases=['northamerica'])
	@commands.guild_only()
	async def NorthAmerica(self, ctx):
		"""Sets the region of the caller to North America"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "North America")
			await ctx.send("Region Set")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "North America", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(aliases=['europe'])
	@commands.guild_only()
	async def Europe(self, ctx):
		"""Sets the region of the caller to Europe"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Europe")
			await ctx.send("Region Set")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Europe", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(aliases=['africa'])
	@commands.guild_only()
	async def Africa(self, ctx):
		"""Sets the region of the caller to Africa"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Africa")
			await ctx.send("Region Set")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Africa", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(aliases=['oceania'])
	@commands.guild_only()
	async def Oceania(self, ctx):
		"""Sets the region of the caller to Oceania"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Oceania")
			await ctx.send("Region Set")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Oceania", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(aliases=['southamerica'])
	@commands.guild_only()
	async def SouthAmerica(self, ctx):
		"""Sets the region of the caller to South America"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "South America")
			await ctx.send("Region Set")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "South America", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(aliases=['asia'])
	@commands.guild_only()
	async def Asia(self, ctx):
		"""Sets the region of the caller to Asia"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Asia")
			await ctx.send("Region Set")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Asia", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command()
	@commands.guild_only()
	async def profilereset(self, ctx):
		"""Resets your profile"""

		query="DELETE FROM profile WHERE user_id = $1"
		await ctx.db.execute(query, ctx.author.id)
		await ctx.send("Profile Reset")

	@commands.command()
	@commands.guild_only()
	async def profileremove(self, ctx, name=None):
		"""Removes an embed field from the profile message"""

		if name is None:
			await ctx.send('Please enter a field to remove')
			return
		else:
			query = "SELECT * FROM Profile WHERE user_id = $1"
			results = await ctx.db.fetch(query, ctx.message.author.id)
			if not results:
				await ctx.send("You have not made your profile yet")
			elif not results[0]['fields']:
				await ctx.send("You have no fields to remove")
			else:
				fields = results[0]['fields']
				for field in fields:
					if field[0] == name:
						fields.remove(field)
						query = "UPDATE Profile SET fields = $1 WHERE user_id = $2"
						await ctx.db.execute(query, fields, ctx.message.author.id)
						await ctx.send("Field Removed")
						return
				await ctx.send("No field with that name")



def check_folders():
	if not os.path.exists("data/rank"):
		print("Creating data/rank folder...")
		os.makedirs("data/rank")


def check_files():
	if not os.path.exists("data/rank/message_data.json"):
		print("Creating data/rank/message_data.json file...")
		dataIO.save_json("data/rank/message_data.json", {})

def setup(bot):
	check_folders()
	check_files()
	bot.add_cog(Profile(bot))
	rank = Rank(bot)
	bot.add_cog(rank)




