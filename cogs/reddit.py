from cogs.utils.dataIO import dataIO
import discord
from discord.ext import commands
from cogs.utils import checks
import requests
from requests.auth import HTTPBasicAuth
import urllib
import json
import asyncio
import os
from datetime import datetime, timedelta
import base64
import uuid

class Reddit:
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'data/reddit/reddit.json'
        self.settings = dataIO.load_json(self.settings_file)
        self.next_item_idx = 0
        self.current_subreddit = ""
        self.current_mode = ""
        self._nextCursor = ""
        self._cache = []
        self.token = False
        self.tokenExpires = False
        self.modes = ["top", "rising", "new", "random", "controversial"]

    async def _ensureAuth(self, ctx):
        if not self.token or self.tokenExpires < datetime.utcnow():
            url = "https://www.reddit.com/api/v1/access_token"
            body = {}
            body["grant_type"] = "https://oauth.reddit.com/grants/installed_client"
            body["device_id"] = self.settings["REDDIT_DEVICE_UUID"]
            response = requests.post(url, body, auth=HTTPBasicAuth(self.settings["REDDIT_API_KEY"], ""), headers = { 'user-agent': 'Yoribot/reddit' })
            if response.status_code == 200:
                self.token = json.loads(response.text)
                self.tokenExpires = datetime.utcnow() + timedelta(seconds=self.token["expires_in"])
                return True
            else:
                print("Reddit Auth Failed {}: {}", response.status_code, response.text )
                await ctx.send("Reddit Auth Failed {}: {} :cry:".format(response.status_code, response.text) )
                return False

    async def _getAndCachePosts(self, ctx, url):
        res = requests.get(url, headers = { 'User-agent': 'Yoribot/reddit', 'Authorization': 'Bearer {}'.format(self.token["access_token"]) })
        if res.status_code != 200:
            print("Error {}: Cannot connect to reddit.com :cry:".format(res.status_code))
            await ctx.send("Error {}: Cannot connect to reddit.com :cry:".format(res.status_code))
            return False

        resJson = json.loads(res.text)

        if "data" in resJson:
            if "children" in resJson["data"]:
                if len(resJson["data"]["children"]) == 0:
                    await ctx.send("Huh... I couldn't find that subreddit.")
                    return False
                else:
                    self._nextCursor = resJson["data"]["after"]
                    self._cache = resJson["data"]["children"]
                    self.next_item_idx = 0
                    return True

    async def _printPost(self, ctx, item):
        embed = discord.Embed(colour=0xff5700, title = item["title"], url="https://www.reddit.com" + item["permalink"])
        if item["thumbnail"] == "self":
            embed.set_thumbnail(url="https://www.redditstatic.com/desktop2x/img/favicon/favicon-96x96.png")
        else:
            embed.set_thumbnail(url=item["thumbnail"])        
        embed.set_author(name="{}".format(item["subreddit_name_prefixed"]), icon_url="https://www.redditstatic.com/desktop2x/img/favicon/favicon-32x32.png")
        author = item['author']
        if item['author_flair_text']:
            author = author + ' `{}`'.format(item['author_flair_text'])
        embed.add_field(name = "Author", value = "u/{} ".format(author))
        if not item['is_self']:
            if 'post_hint' in item:
                if 'post_hint' == 'image':
                    embed.set_image(url=item["url"])
                else:
                    embed.add_field(name="Link", value=item["url"])
        await ctx.send(embed=embed)
        return

    @commands.command(name="reddit")
    async def _reddit(self, ctx, subreddit: str = "$$next_item", mode = "top"):
        '''Gets posts from a provided subreddit on reddit.'''

        if self.settings["REDDIT_API_KEY"]:
            '''Ensure we are authenticated with Reddit'''
            r = await self._ensureAuth(ctx)
            baseUrl = "https://oauth.reddit.com/r/"

            '''Get the guild set prefix for the help message'''
            prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]

            if mode not in self.modes:
                '''Oops someone entered a mode that doesn't exist'''
                await ctx.send("That retrieval mode is invalid. Valid modes are `top`, `random`, `new`, `rising`, `controversial`")
                return
            if subreddit.lower() == "$$next_item":
                if not self.current_subreddit:
                    '''No subreddit selected and someone used the command with no arguments'''
                    await ctx.send("No subreddit currently selected use `{}reddit <subreddit> [mode='top,random,new,rising,controversial']` to set the current subreddit.".format(prefix))
                elif self.next_item_idx == 5:
                    '''Get and Cache the next 5 items from reddit'''
                    url = baseUrl + self.current_subreddit + "/" + self.current_mode + ".json?limit=5&after=" + self._nextCursor
                    t = await self._getAndCachePosts(ctx, url)
                    if not t:
                        '''_getAndCachePosts returns False if there is an error or if the subreddit could not be found.'''
                        self.current_subreddit = ""
                        self.current_mode = ""
                        return
                else:
                    '''We have a set of cached posts to work with'''
                    item = self._cache[self.next_item_idx]["data"]
                    if item["over_18"] and not ctx.message.channel.is_nsfw():
                        '''Self-explanatory. Won't post reddit posts marked as NSFW in an SFW channel'''
                        await ctx.send("Umm... I can't send reddit posts that have been marked as NSFW to an SFW channel.")
                    else:
                        await self._printPost(ctx, item)
                        self.next_item_idx += 1
            else:
                self.current_mode = mode
                self.current_subreddit = subreddit.lower()
                url = baseUrl + self.current_subreddit + "/" + mode + ".json?limit=5"
                t = await self._getAndCachePosts(ctx, url)
                if not t:
                    '''_getAndCachePosts returns False if there is an error or if the subreddit could not be found.'''
                    return
                
                item = self._cache[self.next_item_idx]["data"]
                if item["over_18"] and not ctx.message.channel.is_nsfw():
                    '''Self-explanatory. Won't post reddit posts marked as NSFW in an SFW channel'''
                    await ctx.send("Umm... I can't send reddit posts that have been marked as NSFW to an SFW channel.")
                else:
                    await self._printPost(ctx, item)
                    self.next_item_idx += 1
        else:
            ''' Reddit OAuth Client ID not set'''
            message = 'No API key set. Get one at https://www.reddit.com/prefs/apps'
            await ctx.send('```{}```'.format(message))
            return

    @commands.command(name="redditkey")
    # @checks.is_owner()
    async def _redditkey(self, ctx, key: str):
        """Insert API key into settings"""
        self.settings = dataIO.load_json(self.settings_file)
        self.settings['REDDIT_API_KEY'] = key
        dataIO.save_json(self.settings_file, self.settings)
        await ctx.send('Key saved! It might take a minute or ten before the key is active if you just registered it.')

def check_folder():
    if not os.path.exists("data/reddit"):
        print("Creating data/reddit folder...")
        os.makedirs("data/reddit")


def check_file():
    reddit = {}
    reddit['REDDIT_API_KEY'] = False
    reddit['REDDIT_DEVICE_UUID'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'reddit.yoribot.com'))
    f = "data/reddit/reddit.json"
    if not dataIO.is_valid_json(f):
        print("Creating default reddit.json...")
        dataIO.save_json(f, reddit)


def setup(bot):
    check_folder()
    check_file()
    bot.add_cog(Reddit(bot))