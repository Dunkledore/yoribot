from cogs.utils.dataIO import dataIO
import discord
from discord.ext import commands
from .utils import checks
import requests
import urllib
import json
import asyncio
import os

class Reddit:
    def __init__(self, bot):
      self.bot = bot
      self.settings_file = 'data/reddit/reddit.json'
      self.settings = dataIO.load_json(self.settings_file)
      self.next_item_idx = 0
      self.current_subreddit = ""
      self._nextCursor = ""
      self._cache = []

    async def getAndCachePosts(self, ctx, url):
        r = requests.get(url)
        if r.status_code != 200:
            print("Error {}: Cannot connect to reddit.com :cry:".format(r.status_code))
            # await ctx.send("Error {}: Cannot connect to reddit.com :cry:".format(r.status_code))
            return False

        rJson = json.loads(r.text)

        if ("data" in rJson):
            if ("children" in rJson["data"]):
                if (len(rJson["data"]["children"] == 0)):
                    await ctx.send("Huh... I couldn't find that subreddit.")
                else:
                    self._nextCursor = rJson["after"]
                    self._cache = rJson["children"]

    @commands.command(name="reddit")
    async def _reddit(self, ctx, subreddit: str = "$$next_item", mode = "top"):
        '''Gets posts from a provided subreddit on reddit.'''
        if self.settings['REDDIT_API_KEY']:
            baseUrl = "https://www.reddit.com/r/"
            prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]
            if subreddit.lower() == "$$next_item":
                if not self.current_subreddit:
                    await ctx.send("No subreddit currently selected use `{}reddit <subreddit>` to set the current subreddit.".format(prefix))
                else:
                    item = self._cache[self.next_item_idx]
                    if item["over_18"] and not ctx.message.channel.is_nsfw():
                        ctx.send("I can't send reddit posts that have been marked as NSFW to an SFW channel.")
                    else:
                        embed = discord.Embed(colour=0xff5700, desciption=item["selftext"])
            else:
                url = baseUrl + subreddit.lower + "/" + mode + ".json?limit=5"
                t = await self.getAndCachePosts(ctx, url)
                if not t:
                    return
        else:
            message = 'No API key set. Get one at http://openweathermap.org/'
            await ctx.send('```{}```'.format(message))

    @commands.command(name="redditkey")
    @checks.is_owner()
    async def _redditkey(self, ctx, key: str):

def check_folder():
    if not os.path.exists("data/reddit"):
        print("Creating data/reddit folder...")
        os.makedirs("data/reddit")


def check_file():
    reddit = {}
    reddit['REDDIT_API_KEY'] = False
    f = "data/reddit/reddit.json"
    if not dataIO.is_valid_json(f):
        print("Creating default reddit.json...")
        dataIO.save_json(f, reddit)


def setup(bot):
    n = Reddit(bot)
    bot.add_cog(n)