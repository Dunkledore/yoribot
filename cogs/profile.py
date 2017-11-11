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
		query = "SELECT * FROM profile WHERE guild_id = $1;"
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
			query = "INSERT INTO profile (guild_id, name, value) VALUES ($1, $2, $3)"
		
		try:
			await ctx.db.execute(query, ctx.guild.id, name, value)
		except Exception as e:
			await ctx.send('Field could not be created')
			await ctx.send(e)
		else:
			await ctx.send(f'Field {name} successfully created.')

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	@checks.mod_or_permissions(manage_channels=True)
	async def arraytest(self, ctx):
		"""Adds an embed field onto the profile message"""
		
		await ctx.send("doing")
		query = "INSERT INTO test (values) VALUES ($1)"
		mylist = [ctx.message.content,"value"]
		await ctx.db.execute(query, mylist)
		await ctx.send("done")

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




