from .utils import db, checks, formats, cache
from .utils.paginator import Pages

from discord.ext import commands
from .utils.chat_formatting import box
import json
import re
import datetime
import requests
import discord
import asyncio
import traceback
import asyncpg
import psutil
import tweepy
import os

class SocialMedia:
	"""Commands used to set up your server profile"""

	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.api_cache = []

	def get_api(self, creds):
		for api in self.api_cache:
			if api[0] == creds[0]:
				return api[1];
		auth = tweepy.OAuthHandler(creds[0], creds[1])
		auth.set_access_token(creds[2], creds[3])
		api = tweepy.API(auth)
		self.api_cache.append([creds[0], api])
		return api

	async def get_creds(self, guild):
		query = "SELECT * FROM social_config WHERE guild_id = $1"
		creds = await self.bot.pool.fetch(query, guild.id)
		if creds:
			if creds[0]:
				return creds[0]["twitter"]
		return None


	def tweetToEmbed(self, tweet):
		em = discord.Embed(title="Follow Us on Twitter", url=tweet.user.url ,color=discord.Colour.teal())
		em.set_author(name=tweet.user.name, icon_url=tweet.user.profile_image_url)
		em.add_field(name="Tweet", value=tweet.text)
		em.set_footer(text="Followers:" + tweet.user.followers_count + "Following:" + tweet.user.friends_count + "Tweets:" + tweet.user.statuses_count)
		if 'media' in tweet.entities:
			if tweet.entities['media'][0]['type'] == 'photo':
				em.set_image(url=tweet.entities['media'][0]['media_url_https'])
		return em



	async def feeds(self):
		await self.bot.wait_until_ready()
		while True:
			try:
				query = "SELECT guild_id, feed_channel, last_tweet FROM social_config"
				results = await self.bot.pool.fetch(query)
				for result in results:
					if not result["feed_channel"]:
						continue
					creds = await self.get_creds(self.bot.get_guild(result["guild_id"]))
					print('got creds')
					if not creds:
						continue
					api = self.get_api(creds)
					me = api.me()
					if not result["last_tweet"]:
						tweets = api.user_timeline(id=me.id,count=20)
					else:
						tweets = api.user_timeline(id=me.id,since_id=result["last_tweet"])

					tweet_id = result["last_tweet"]
					for tweet in reversed(tweets):
						channel = self.bot.get_channel(result["feed_channel"])
						await channel.send(embed=self.tweetToEmbed(tweet))
						tweet_id = tweet.id

					insertquery = "INSERT INTO social_config (guild_id, last_tweet) VALUES ($1, $2)"
					alterquery = "UPDATE social_config SET last_tweet = $2 WHERE guild_id = $1"

					try:
						await self.bot.pool.execute(insertquery, result["guild_id"], tweet_id)
					except asyncpg.UniqueViolationError:
						await self.bot.pool.execute(alterquery, result["guild_id"], tweet_id)
			except Exception as e:
				"""Fail Silently"""

			await asyncio.sleep(61)


	@commands.group(no_pm=True)
	@checks.is_developer()
	async def twitterset(self, ctx):
		"""Admin twitter related commands"""

		if ctx.invoked_subcommand is None:
			
			query = "SELECT * FROM social_config WHERE guild_id = $1"
			results = await self.bot.pool.fetch(query, ctx.guild.id)
			if results is None:
				tweeter_role = tweeter_number = 0
			elif len(results) == 0:
				tweeter_role = tweeter_number = 0
			else:
				tweeter_role = results[0]["tweeter_role_id"]
				tweeter_number = results[0]["tweeter_reaction"]
				feed_channel = results[0]["feed_channel"]
			msg = box("Reactions until tweet: {0} 🐦\n"
					  "Tweeter role ID:  {1}\n"
					  "Twitter Feed Channel {2}\n"
					  .format(tweeter_number or "0", tweeter_role or "0", str(self.bot.get_channel(feed_channel)) or "OFF"))
			msg += "\n {}twittetset tweeter <role>".format(ctx.prefix)
			msg += "\n {}twitterset tweetnumber <number>".format(ctx.prefix)
			msg += "\n {}twitterset tweetcreds".format(ctx.prefix)
			msg += "\n {}twitterset feedchannel <channel>".format(ctx.prefix)
			em = discord.Embed(color=ctx.message.author.color, description=msg)
			em.set_author(name="Twitter Settings Help", icon_url="http://bit.ly/2qrhjLu")
			await ctx.send(embed=em)
			

	@twitterset.command(hidden=True)
	async def feedchannel(self, ctx, channel : discord.TextChannel):


		insertquery = "INSERT INTO social_config (guild_id, feed_channel) VALUES ($1, $2)"
		alterquery = "UPDATE social_config SET feed_channel = $2 WHERE guild_id = $1"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, channel.id)
		await ctx.send('Channel Set')
	
	@twitterset.command(hidden=True)
	async def tweetnumber(self, ctx, number: int):
		"""Sets the number of bird reactions required to tweet something"""

		insertquery = "INSERT INTO social_config (guild_id, tweeter_reaction) VALUES ($1, $2)"
		alterquery = "UPDATE social_config SET tweeter_reaction = $2 WHERE guild_id = $1"

		try:
			await ctx.db.execute(insertquery, ctx.guild.id, number)
		except asyncpg.UniqueViolationError:
			await ctx.db.execute(alterquery, ctx.guild.id, number)
		await ctx.send('Number set')

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
		if ctx.message.attachments:
			if ctx.message.attachments[0].height:
				filename = 'temp.jpg'
				request = requests.get(ctx.message.attachments[0].url, stream=True)
				if request.status_code == 200:
					with open(filename, 'wb') as image:
						for chunk in request:
							image.write(chunk)

			await self.sendtweet(ctx.guild, tweet, ctx, filename)
			await ctx.message.delete()
			await ctx.send("Tweet Tweeted")
			return
		
		await self.sendtweet(ctx.guild, tweet, ctx)		
		await ctx.message.delete()
		await ctx.send("Tweet Tweeted")
	

	async def sendtweet(self, guild, tweet, ctx=None, attatchment=None):
		creds = await self.get_creds(guild)
		if not creds:
			if ctx is None:
				return
			else:
				await ctx.send("Your guild owner has not setup twitter credentials")
		else:
			api = self.get_api(creds)

			if attatchment:
				status = api.update_with_media(attatchment, status=tweet)
				os.remove(attatchment)
			else:
				status = api.update_status(status=tweet)
 

	async def on_reaction_add(self, reaction, user):
		if reaction.emoji != "🐦" or reaction.message.channel.is_nsfw():
			return

		query = "SELECT * FROM social_config WHERE guild_id = $1"
		results = await self.bot.pool.fetch(query, reaction.message.guild.id)
		tweeter_role = results[0]["tweeter_role_id"]
		for role in user.roles:
			if role.id == tweeter_role or reaction.count >= results[0]["tweeter_reaction"]:

				if reaction.message.attachments:
					if reaction.message.attachments[0].height:
						filename = 'temp.jpg'
						request = requests.get(reaction.message.attachments[0].url, stream=True)
						if request.status_code == 200:
							with open(filename, 'wb') as image:
								for chunk in request:
									image.write(chunk)
					await self.sendtweet(reaction.message.guild, reaction.message.clean_content + '-' + reaction.message.author, None, filename)
					return

				await self.sendtweet(reaction.message.guild, reaction.message.clean_content + '-' + reaction.message.author)

		


def setup(bot):
	n = SocialMedia(bot)
	bot.add_cog(n)
	bot.loop.create_task(n.feeds())




