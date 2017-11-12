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
		"""Will send the welcome message as if the caller just joined"""
		await self.show_welcome_message(ctx)

	async def show_profile(self, ctx):
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
			await ctx.send(results[6])
			if not results:
				fields = [[name,value]]
				query = "INSERT INTO Profile (guild_id, user_id, fields) VALUES ($1, $2, $3)"
				await ctx.db.execute(query, ctx.guild.id, ctx.message.author.id, fields)
				await ctx.send("Field Added")
			elif not results[7]:
				fields = [[name,value]]
				query = "UPDATE Profile SET fields = $1 WHERE user_id = $2"
				await ctx.db.execute(query, fields, ctx.message.author.id)
			else:
				fields = results[7]
				fields.append([name,value])
				query = "UPDATE Profile SET fields = $1 WHERE user_id = $2"
				await ctx.db.execute(query, fields, ctx.message.author.id)



	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
	async def arraytest(self, ctx):
		"""Adds an embed field onto the profile message"""
		
		await ctx.send("doing")
		query = "INSERT INTO test (values) VALUES ($1)"
		mylist = [ctx.message.content,"value"]
		await ctx.db.execute(query, mylist)
		await ctx.send("done")
		query = "SELECT * FROM test"
		rows = await ctx.db.fetch(query)
		for r in rows:
			await ctx.send(r)

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
	async def profileremove(self, ctx, name=None):
		"""Removes and embed field from the profile message"""

		if name is None:
			await ctx.send('Please enter a field to remove')
			return
		else:
			query = "DELETE FROM profile WHERE guild_id =$1 AND name = $2"
			await ctx.db.execute(query, ctx.guild.id, name)
			await ctx.send('Field Removed')

def setup(bot):
    bot.add_cog(Profile(bot))




