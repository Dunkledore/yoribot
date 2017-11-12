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
	@checks.mod_or_permissions(manage_channels=True)
	async def profile(self, ctx):
		
		query = "SELECT * FROM profile WHERE user_id = $1;"
		profile = await ctx.db.fetch(query, ctx.guild.id)
		embed = discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.set_author(name=ctx.message.author.name, icon_url=ctx.message.guild.icon_url)
		embed.set_thumbnail(url=ctx.message.author.avatar_url)

		for fields in profile:
			embed.add_field(name=fields[2], value=fields[3].format(ctx.message.author))


		await ctx.send(embed=embed)

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
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
			elif not results[0][7]:
				fields = [[name,value]]
				query = "UPDATE Profile SET fields = $1 WHERE user_id = $2"
				await ctx.db.execute(query, fields, ctx.message.author.id)
				await ctx.send("Field added")
			else:
				fields = results[0][7]
				fields.append([name,value])
				query = "UPDATE Profile SET fields = $1 WHERE user_id = $2"
				await ctx.db.execute(query, fields, ctx.message.author.id)
				await ctx.send("Field added")


	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
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
			elif not results[0][7]:
				await ctx.send("You have no fields to remove")
			else:
				fields = results[0][7]
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




