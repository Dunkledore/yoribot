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

class Profile:
	"""Commands used to set up your server profile"""

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	async def profile(self, ctx, user: discord.Member=None):
		"""Displays the profile of a mentioned user or the caller if no mention is provided"""

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

		for fields in profile[0]['fields']:
			embed.add_field(name=fields[0], value=fields[1].format(ctx.message.author))


		await ctx.send(embed=embed)

	@commands.command(pass_context=True, no_pm=True, hidden=True)
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

	@commands.command(pass_context=True, no_pm=True, hidden=True)
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

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	async def gender(self, ctx, gender):
		"""Sets the age of the caller"""

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

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	async def sexuality(self, ctx, sexuality):
		"""Sets the age of the caller"""

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




