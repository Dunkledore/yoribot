import discord
from discord.ext import commands
import asyncio
import aiohttp
import random
try:
    from bs4 import BeautifulSoup
    hasSoup = True
except:
    hasSoup = False

class Comics:

    async def xkcd():
        """Randomly retrieve and display a comic from xkcd"""
        url = "https://c.xkcd.com/random/comic/" #build the web adress
        async with aiohttp.get(url) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
            url = response.url
            titleFinder = soupObject
            ctitle = titleFinder.find("div", id="ctitle")
            title = ctitle.contents[0]
            comic = soupObject.find(id="comic")
            img = comic.find("img")
            caption = img["title"]
            imgurl = "https:{}".format(img["src"])
            em = discord.Embed(title=title, description=caption,url=url, colour=0x002eff)
            em.set_image(url=imgurl)
            em.set_author(name='xkcd.com', icon_url="https://xkcd.com/s/0b7742.png")
            return em

    async def cnh():
        """Randomly retrieve and display a comic from Cyanide and Happiness"""
        url = "http://explosm.net/comics/random" #build the web adress
        async with aiohttp.get(url) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
            url = response.url
            img = soupObject.find(id="main-comic")
            imgurl = "https:{}".format(img["src"])
            em = discord.Embed(title="Cyanide and Happiness",url=url, colour=0xefc62f)
            em.set_image(url=imgurl)
            em.set_author(name='explosm.net', icon_url="http://explosm.net/img/logo.png")
            return em

    async def se():
        """Randomly retrieve and display a comic from Safely Endangered"""
        url = "http://www.safelyendangered.com/?random&nocache=1" #build the web adress
        async with aiohttp.get(url) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
            url = response.url
            comic = soupObject.find(id="comic")
            comic = comic.find("img")
            heading = soupObject.find_all("h2", class_="post-title")
            title = heading[0].contents[0]
            imgurl = comic["src"]
            em = discord.Embed(title=title, url=url, colour=0x2a2a2b)
            em.set_image(url=imgurl)
            em.set_author(name='safelyendangered.com', icon_url="http://www.safelyendangered.com/wp-content/uploads/2016/01/safely-endangered-comics-1.png")
            return em


class Funny:
    """Get a funny comic"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['funnyx', 'fx'])
    async def xkcd(self, ctx):
        """Randomly retrieve and display a comic from xkcd"""
        try:
            em = await Comics.xkcd()
            await ctx.send(embed = em)
        except:
            await ctx.send("Could not load comic")
            raise

    @commands.command(aliases=['funnyc', 'fc'])
    async def cnh(self, ctx):
        """Randomly retrieve and display a comic from Cyanide and Happiness"""
        try:
            em = await Comics.cnh()
            await ctx.send(embed = em)
        except:
            await ctx.send("Could not load comic")
            raise

    @commands.command(aliases=['funnys', 'fs'])
    async def se(self, ctx):
        """Randomly retrieve and display a comic from Safely Endangered"""
        try:
            em = await Comics.se()
            await ctx.send(embed = em)
        except:
            await ctx.send("Could not load comic")
            raise

    @commands.command(aliases=['fr', "bored"])
    async def funnyr(self, ctx):
        """Randomly Retrieves a comic from one of the sources"""
        random.seed()
        rand = random.randint(0 , 2)
        try:
            if(rand == 0):
                em = await Comics.cnh()
                await ctx.send(embed = em)
            elif(rand == 1):
                em = await Comics.xkcd()
                await ctx.send(embed = em)
            elif(rand == 2):
                em = await Comics.se()
                await ctx.send(embed = em)
            else:
                await ctx.send("Thats odd you shouldn't be seeing this")
        except:
            await ctx.send("Could not load comic")
            raise


def setup(bot):
    if hasSoup:
        n=Funny(bot)
        bot.add_cog(n)
    else:
        print("Install BeautifulSoup4 using pip install BeautifulSoup4")