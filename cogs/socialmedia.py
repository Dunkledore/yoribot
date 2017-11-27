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
import tweepy

class SocialMedia:
	"""Commands used to set up your server profile"""

	def __init__(self, bot: commands.Bot):
		self.bot = bot

	def get_api(self, consumer_key, consumer_secret, access_token, access_token_secret):
		auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
		auth.set_access_token(access_token, access_token_secret)
		return tweepy.API(auth)

	async def get_creds(self, ctx):
		query = "SELECT * FROM social_config WHERE guild_id = $1"
		creds = await ctx.db.fetch(query, ctx.guild.id)
		if creds:
			if creds[0]:
				return creds[0]["twitter"]
		return None


	
	@commands.group(no_pm=True)
	@checks.is_developer()
	async def twitterset(self,ctc):
		a=1

	
	@twitterset.command(hidden=True)
	async def tweetnumber(self, ctx, number: int):
		"""Sets the number of bird reactions required to tweet something"""

		insertquery = "INSERT INTO social_config (guild_id, tweeter_reaction) VALUES ($1, $2)"
		alterquery = "UPDATE social_config SET tweeter_reaction = $2 WHERE guild_id = $1"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, number)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, number)
		await ctx.send('Role set')

	@twitterset.command(hidden=True)
	async def tweeter(self, ctx, role: discord.Role):
		"""Sets the mod role"""

		insertquery = "INSERT INTO social_config (guild_id, tweeter_role_id) VALUES ($1, $2)"
		alterquery = "UPDATE social_config SET tweeter_role_id = $2 WHERE guild_id = $1"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, role.id)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, role.id)
		await ctx.send('Role set')

	@twitterset.command()
	async def tweetcreds(self, ctx):

		async def check(m):
			return m.author == ctx.author

		await ctx.author.send("Please send your cosumer key")
		consumer_key = await self.bot.wait_for('message', check=check, timeout=30.0)

		await ctx.author.send("Please send your consumer secret")
		consumer_secret = await self.bot.wait_for('message', check=check, timeout=30.0)

		await ctx.author.send("Please send your access token")
		access_token = await self.bot.wait_for('message', check=check, timeout=30.0)

		await ctx.author.send("Please send your access token secret")
		access_token_secret = await self.bot.wait_for('message', check=check, timeout=30.0)

		insertquery = "INSERT INTO social_config (guild_id, twitter) VALUES ($1, $2)"
		alterquery = "UPDATE  SET twitter = $2 WHERE guild_id = $1"

		twitter_creds = [consumer_key,consumer_secret,access_token,access_token_secret]

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, twitter_creds)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, twitter_creds)
		await ctx.author.send('Details Saved')


	@commands.command(no_pm=True)
	@checks.is_tweeter()
	async def tweet(self, ctx, *, tweet):
		
		creds = await self.get_creds(ctx)
		if not creds:
			await ctx.send("Your guild owner has not setup twitter credentials")
		else:
			api = get_api(creds)
			status = api.update.stauts(status = tweet)
			await ctx.messgae.delete()

def setup(bot):
	bot.add_cog(SocialMedia(bot))




