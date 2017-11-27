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

	def get_api(self, creds):
		auth = tweepy.OAuthHandler(creds[0], creds[1])
		auth.set_access_token(creds[2], creds[3])
		return tweepy.API(auth)

	async def get_creds(self, guild):
		query = "SELECT * FROM social_config WHERE guild_id = $1"
		creds = await self.bot.pool.fetch(query, guild.id)
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

		author = ctx.author
		def check(m):
			return m.author == author

		await ctx.author.send("Please send your cosumer key")
		consumer_key = await self.bot.wait_for('message', check=check, timeout=30.0)
		consumer_key = consumer_key.content
		await asyncio.sleep(1)

		await ctx.author.send("Please send your consumer secret")
		consumer_secret = await self.bot.wait_for('message', check=check, timeout=30.0)
		consumer_secret = consumer_secret.content
		await asyncio.sleep(1)

		await ctx.author.send("Please send your access token")
		access_token = await self.bot.wait_for('message', check=check, timeout=30.0)
		access_token = access_token.content
		await asyncio.sleep(1)

		await ctx.author.send("Please send your access token secret")
		access_token_secret = await self.bot.wait_for('message', check=check, timeout=30.0)
		access_token_secret = access_token_secret.content

		insertquery = "INSERT INTO social_config (guild_id, twitter) VALUES ($1, $2)"
		alterquery = "UPDATE social_config SET twitter = $2 WHERE guild_id = $1"

		twitter_creds = [consumer_key,consumer_secret,access_token,access_token_secret]

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, twitter_creds)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, twitter_creds)
		await ctx.author.send('Details Saved')

	@commands.command(no_pm=True)
	@checks.is_tweeter()
	async def tweet(self, ctx, *, tweet):
		await self.sendtweet(ctx.guild, tweet)
		await ctx.message.delete()
		await ctx.send("Tweet Tweeted")
	

	async def sendtweet(self, guild, tweet, ctx=None):
		creds = await self.get_creds(guild)
		if not creds:
			if ctx is None:
				return
			else:
				await ctx.send("Your guild owner has not setup twitter credentials")
		else:
			api = self.get_api(creds)
			status = api.update_status(status=tweet)


	async def on_reaction_add(self, reaction, user):
		if reaction.emoji != "🐦":
			return

		query = "SELECT * FROM social_config WHERE guild_id = $1"
		results = await self.bot.pool.fetch(query, reaction.message.guild.id)
		tweeter_role = results[0]["tweeter_role_id"]
		for role in user.roles:
			if role.id == tweeter_role:
				await self.sendtweet(reaction.message.guild, reaction.message.content)
				return

		if reaction.count >= results[0]["tweeter_reaction"]:
			self.sendtweet(reaction.message.guild, reaction.message.content)

		


def setup(bot):
	bot.add_cog(SocialMedia(bot))




