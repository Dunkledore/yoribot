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
import io
from datetime import datetime, timedelta
import base64
import uuid

class Reddit:
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'data/reddit/reddit.json'
        self.settings = dataIO.load_json(self.settings_file)
        self.next_item_idx = {}
        self.max_item_idx = {}
        self.current_subreddit = {}
        self.current_mode = {}
        self._nextCursor = {}
        self._cache = {}
        self.token = False
        self.tokenExpires = False
        self.tasks = []
        self.modes = ["top", "rising", "new", "random", "controversial", "hot"]

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
            if res.status_code == 403:
                await ctx.send("That subreddit is invite only I can't get posts from it.")
                return False
            print("Error {}: Cannot connect to reddit.com :cry:".format(res.status_code))
            await ctx.send("Error {}: Cannot connect to reddit.com :cry:".format(res.status_code))
            return False

        resJson = json.loads(res.text)

        if "data" in resJson:
            if "dist" in resJson["data"]:
                self.max_item_idx[ctx.message.guild][ctx.message.author] = resJson["data"]["dist"]
            if "children" in resJson["data"]:
                if len(resJson["data"]["children"]) == 0:
                    await ctx.send("Huh... I couldn't find that subreddit.")
                    return False
                else:
                    if "after" in resJson["data"]:
                        self._nextCursor[ctx.message.guild][ctx.message.author] = resJson["data"]["after"]
                    self._cache[ctx.message.guild][ctx.message.author] = resJson["data"]["children"]
                    self.next_item_idx[ctx.message.guild][ctx.message.author] = 0
                    return True
    
    async def _disambiguate(self, ctx, items):
        resEmbed = discord.Embed(title="**Choose One by giving it's number**", colour=0xff5700)
        resEmbed.set_footer(text="Subreddit Search Results")
        for i in range(len(items[0:5])):
            badge = " `NSFW` " if items[i]["data"]["over18"] else " "
            strI = str(i + 1 * 5 -4)  + ". " + items[i]["data"]["display_name_prefixed"] + badge + items[i]["data"]["title"]
            resEmbed.add_field(name=strI, value="https://www.reddit.com"+items[i]["data"]["url"])
        
        await ctx.send(embed=resEmbed)

        def check(m):
            if m.author != ctx.message.author:
                return False
            if m.channel != ctx.message.channel:
                return False
            return m.content in map(str, range(1, 6))
        
        self.tasks.append(asyncio.ensure_future(self.bot.wait_for('message', check=check,timeout=20)))
        resp = await self.tasks[len(self.tasks)-1]

        selectedIndex = (int(resp.content)-1)
        selectedItem = items[selectedIndex]

        if not selectedItem:
            await ctx.send("couldn't get your subreddit for some reason")
            return

        self.current_subreddit[ctx.message.guild][ctx.message.author] = selectedItem["data"]["display_name_prefixed"][2:].lower()
        url = "https://oauth.reddit.com/r/" + self.current_subreddit[ctx.message.guild][ctx.message.author] + "/" + self.current_mode[ctx.message.guild][ctx.message.author] + ".json?limit=5"
        t = await self._getAndCachePosts(ctx, url)
        if not t:
            return
        item = self._cache[ctx.message.guild][ctx.message.author][self.next_item_idx[ctx.message.guild][ctx.message.author]]["data"]

        if "subscribers" in item:
            await self._disambiguate(ctx, self._cache[ctx.message.guild][ctx.message.author])
        elif item["over_18"] and not ctx.message.channel.is_nsfw():
            '''Self-explanatory. Won't post reddit posts marked as NSFW in an SFW channel'''
            await ctx.send("Umm... I can't send reddit posts that have been marked as NSFW to an SFW channel.")
        else:
            await self._printPost(ctx, item)
            self.next_item_idx[ctx.message.guild][ctx.message.author] += 1



    async def _printPost(self, ctx, item):
        embed = discord.Embed(colour=0xff5700, title = item["title"], url="https://www.reddit.com" + item["permalink"], description=item["selftext"])
        if item["thumbnail"] == "self" or item["thumbnail"] == "":
            embed.set_thumbnail(url="https://www.redditstatic.com/desktop2x/img/favicon/favicon-96x96.png")
        else:
            embed.set_thumbnail(url=item["thumbnail"])        
        
        author = item['author']
        if item['author_flair_text']:
            author = author + ' `{}`'.format(item['author_flair_text'])
        embed.set_author(name="{} • u/{}".format(item["subreddit_name_prefixed"], author), icon_url="https://www.redditstatic.com/desktop2x/img/favicon/favicon-32x32.png")

        embed.add_field(name= "Score", value=str(item["score"]) + "  ({}:arrow_up_small: {}:arrow_down_small:)".format(item["ups"], item["downs"]))
        if not item['is_self']:
            if 'post_hint' in item:
                if item['post_hint'] == 'image':
                    embed.set_image(url=item["url"])
                elif item['post_hint'] == 'link' and item['domain'] == 'imgur.com':
                    embed.set_image(url=item["url"]+".png")
                else:
                    embed.add_field(name="Link", value=item["url"])
        embed.set_footer(text=datetime.utcfromtimestamp(item["created_utc"]).strftime("%A,  %d. %B %Y %I:%M%p %Z"))
        await ctx.send(embed=embed)
        return

    @commands.command(name="reddit")
    async def _reddit(self, ctx, subreddit: str = None, mode = "hot"):
        '''Gets posts from a provided subreddit on reddit.'''
        if ctx.message.guild not in self.current_subreddit:
            self.current_subreddit[ctx.message.guild] = {}
        if ctx.message.author not in self.current_subreddit[ctx.message.guild]:
            self.current_subreddit[ctx.message.guild][ctx.message.author] = False
        
        if ctx.message.guild not in self.current_mode:
            self.current_mode[ctx.message.guild] = {}
        if ctx.message.author not in self.current_mode[ctx.message.guild]:
            self.current_mode[ctx.message.guild][ctx.message.author] = ""

        if ctx.message.guild not in self._nextCursor:
            self._nextCursor[ctx.message.guild] = {}
        if ctx.message.author not in self._nextCursor[ctx.message.guild]:
            self._nextCursor[ctx.message.guild][ctx.message.author] = ""
        
        if ctx.message.guild not in self._cache:
            self._cache[ctx.message.guild] = {}
        if ctx.message.author not in self._cache[ctx.message.guild]:
            self._cache[ctx.message.guild][ctx.message.author] = []

        if ctx.message.guild not in self.next_item_idx:
            self.next_item_idx[ctx.message.guild] = {}
        if ctx.message.author not in self.next_item_idx[ctx.message.guild]:
            self.next_item_idx[ctx.message.guild][ctx.message.author] = 0
        if ctx.message.guild not in self.max_item_idx:
            self.max_item_idx[ctx.message.guild] = {}
        if ctx.message.author not in self.next_item_idx[ctx.message.guild]:
            self.max_item_idx[ctx.message.guild][ctx.message.author] = 0
        if self.settings["REDDIT_API_KEY"]:
            '''Ensure we are authenticated with Reddit'''
            r = await self._ensureAuth(ctx)
            baseUrl = "https://oauth.reddit.com/r/"

            if mode and mode not in self.modes:
                '''Oops someone entered a mode that doesn't exist'''
                await ctx.send("That retrieval mode is invalid. Valid modes are `top`, `random`, `new`, `rising`, `controversial`, `hot`")
                return
            if subreddit.lower() is None:
                if not self.current_subreddit[ctx.message.guild][ctx.message.author]:
                    '''No subreddit selected and someone used the command with no arguments'''
                    embed = discord.Embed(color=ctx.message.author.color, title="❔ Help", description="For help with this command please use ``reddithelp``")
                    await ctx.send()
                elif self.next_item_idx[ctx.message.guild][ctx.message.author] == self.max_item_idx[ctx.message.guild][ctx.message.author]:
                    '''Get and Cache the next 5 items from reddit'''
                    if not self._nextCursor[ctx.message.guild][ctx.message.author]:
                        await ctx.send("No more posts found")
                        return
                    url = baseUrl + self.current_subreddit[ctx.message.guild][ctx.message.author] + "/" + self.current_mode[ctx.message.guild][ctx.message.author] + ".json?limit=5&after=" + self._nextCursor[ctx.message.guild][ctx.message.author]
                    t = await self._getAndCachePosts(ctx, url)
                    if not t:
                        '''_getAndCachePosts returns False if there is an error or if the subreddit could not be found.'''
                        self.current_subreddit[ctx.message.guild][ctx.message.author] = ""
                        self.current_mode[ctx.message.guild][ctx.message.author] = ""
                        return
                    item = self._cache[ctx.message.guild][ctx.message.author][self.next_item_idx[ctx.message.guild][ctx.message.author]]["data"]
                    if item["over_18"] and not ctx.message.channel.is_nsfw():
                        '''Self-explanatory. Won't post reddit posts marked as NSFW in an SFW channel'''
                        await ctx.send("Umm... I can't send reddit posts that have been marked as NSFW to an SFW channel.")
                    else:
                        await self._printPost(ctx, item)
                        self.next_item_idx[ctx.message.guild][ctx.message.author] += 1
                else:
                    '''We have a set of cached posts to work with'''
                    if self.max_item_idx[ctx.message.guild][ctx.message.author] > self.next_item_idx[ctx.message.guild][ctx.message.author]:
                        item = self._cache[ctx.message.guild][ctx.message.author][self.next_item_idx[ctx.message.guild][ctx.message.author]]["data"]
                        if item["over_18"] and not ctx.message.channel.is_nsfw():
                            '''Self-explanatory. Won't post reddit posts marked as NSFW in an SFW channel'''
                            await ctx.send("Umm... I can't send reddit posts that have been marked as NSFW to an SFW channel.")
                        else:
                            await self._printPost(ctx, item)
                            self.next_item_idx[ctx.message.guild][ctx.message.author] += 1
                    else:
                        await ctx.send("No other posts found")
            else:
                self.current_mode[ctx.message.guild][ctx.message.author] = mode
                self.current_subreddit[ctx.message.guild][ctx.message.author] = subreddit.lower()
                url = baseUrl + self.current_subreddit[ctx.message.guild][ctx.message.author] + "/" + mode if mode else "" + ".json?limit=5"
                t = await self._getAndCachePosts(ctx, url)
                if not t:
                    '''_getAndCachePosts returns False if there is an error or if the subreddit could not be found.'''
                    return
                
                item = self._cache[ctx.message.guild][ctx.message.author][self.next_item_idx[ctx.message.guild][ctx.message.author]]["data"]
                if "subscribers" in item:
                    await self._disambiguate(ctx, self._cache[ctx.message.guild][ctx.message.author])
                elif item["over_18"] and not ctx.message.channel.is_nsfw():
                    '''Self-explanatory. Won't post reddit posts marked as NSFW in an SFW channel'''
                    await ctx.send("Umm... I can't send reddit posts that have been marked as NSFW to an SFW channel.")
                else:
                    await self._printPost(ctx, item)
                    self.next_item_idx[ctx.message.guild][ctx.message.author] += 1
        else:
            ''' Reddit OAuth Client ID not set'''
            message = 'No API key set. Get one at https://www.reddit.com/prefs/apps'
            await ctx.send('```{}```'.format(message))
            return

    @commands.command(name="reddithelp")
    async def _reddithelp(self, ctx):
        pass

    @commands.command(name="redditkey")
    @checks.is_owner()
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