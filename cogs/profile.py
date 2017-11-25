from .utils import db, checks, formats, cache
from .utils.paginator import Pages

from discord.ext import commands
import json
import re
import datetime
import discord
import asyncio
import traceback
import asyncpg
import psutil

class Profile:
	"""Commands used to set up your server profile"""

	def __init__(self, bot: commands.Bot):
		self.bot = bot
	
	@commands.command()
	async def profilehelp(self, ctx):
		prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]
		em = discord.Embed(color=ctx.message.author.color, description="Need help setting up your profile? No worries, here are some pointers:")
		em.set_author(name="Profile Setup Help", icon_url="http://yoribot.com/wp-content/uploads/2017/11/yoriicon.png")
		em.add_field(name='Adding Your Region', value='Use one of the following commands: \n\n `` ' + prefix + 'north america`` `` ' + prefix + 'south america`` `` ' + prefix + 'europe`` `` ' + prefix + 'africa`` `` ' + prefix + 'asia`` `` ' + prefix + 'oceania``', inline=False)
		em.add_field(name='Adding Gender', value='Use `` ' + prefix + 'gender <gender>`` for example:\n\n `` ' + prefix + 'gender Male`` or `` ' + prefix + 'gender Female`` or `` ' + prefix + 'genderntersex`` ', inline=False)
		em.add_field(name='Adding Sexuality', value='Use `` ' + prefix + 'sexuality <sexuality> for example: \n\n `` `` ' + prefix + 'sexuality Straight`` `` ' + prefix + 'sexuality Gay`` `` ' + prefix + 'sexuality Lesbian`` `` ' + prefix + 'sexuality Asexual``', inline=False)
		em.add_field(name='Adding Age', value='Use `` ' + prefix + 'age <age> for example: \n\n `` ``' + prefix + 'age 20``.', inline=False)
		em.add_field(name='Custom Fields', value='You can add custom sections to your profile using \n\n`` ' + prefix + 'profileadd <section title> <contents>``\n'
					'\nFor example you might do: \n\n``' + prefix +'profileadd "About Me" I am a one of the best Discord bots around - I am easy to use and I have a ton of fun features!``\n', inline=False)
		em.set_footer(text= "Use the help command or visit http://yoribot.com for more information.")
		await ctx.send(embed=em)

	async def sendYori(self, ctx):

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
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(name='Process', value=f'{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU')
        embed.add_field(name='Guilds', value=len(self.bot.guilds))
        embed.add_field(name='Commands Run', value=sum(self.bot.command_stats.values()))
        embed.add_field(name='Uptime', value=self.get_bot_uptime(brief=True))
        embed.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')
		await ctx.send(embed=embed)

	@commands.command(pass_context=True, no_pm=True)
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

	@commands.command(pass_context=True, no_pm=True)
	async def profileadd(self, ctx, name=None, *, value=None):
		"""Adds an embed field onto the profile message"""
		
		if (name is None) or (value is None):
			await ctx.send('Please enter both a field and a value')
			return
		else:
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

	@commands.command(pass_context=True, no_pm=True)
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

	@commands.command(pass_context=True, no_pm=True)
	async def gender(self, ctx, gender):
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

	@commands.command(pass_context=True, no_pm=True)
	async def sexuality(self, ctx, sexuality):
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

	@commands.command(pass_context=True, no_pm=True, aliases=['northamerica'])
	async def NorthAmerica(self, ctx):
		"""Sets the region of the caller to North America"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "North America")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "North America", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(pass_context=True, no_pm=True, aliases=['europe'])
	async def Europe(self, ctx):
		"""Sets the region of the caller to Europe"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Europe")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Europe", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(pass_context=True, no_pm=True, aliases=['africa'])
	async def Africa(self, ctx):
		"""Sets the region of the caller to Africa"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Africa")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Africa", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(pass_context=True, no_pm=True, aliases=['oceania'])
	async def Oceania(self, ctx):
		"""Sets the region of the caller to Oceania"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Oceania")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Oceania", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(pass_context=True, no_pm=True, aliases=['southamerica'])
	async def SouthAmerica(self, ctx):
		"""Sets the region of the caller to South America"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "South America")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "South America", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(pass_context=True, no_pm=True,  aliases=['asia'])
	async def Asia(self, ctx):
		"""Sets the region of the caller to Asia"""

		query = "SELECT * FROM Profile WHERE user_id = $1"
		results = await ctx.db.fetch(query, ctx.message.author.id)
		if not results:
			query = "INSERT INTO Profile (guild_id, user_id, region) VALUES ($1, $2, $3)"
			await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, "Asia")
		else:
			query = "UPDATE Profile SET region = $1 WHERE user_id = $2"
			await ctx.db.execute(query, "Asia", ctx.message.author.id)
			await ctx.send("Region Set")

	@commands.command(pass_context=True, no_pm=True)
	async def profiledelete(self, ctx):
		"""Removes and embed field from the profile message"""

		query="DELETE FROM profile WHERE user_id = $1"
		await ctx.db.execute(query, ctx.author.id)
		await ctx.send("Profile Deleted")

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	async def profileremove(self, ctx, name=None):
		"""Removes and embed field from the profile message"""

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


def setup(bot):
	bot.add_cog(Profile(bot))




