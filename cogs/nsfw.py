import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import random
from .utils import checks
import aiohttp

class Nsfw:
    """Nsfw commands."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @commands.group(pass_context=True, hidden=True)
    @checks.is_nsfw()
    async def nsfw(self, ctx):
        """Nsfw Commands"""

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def yandere(self, ctx):
        """Random Image From Yandere"""
        try:
            query = ("https://yande.re/post/random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="highres").get("href")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def konachan(self, ctx):
        """Random Image From Konachan"""
        try:
            query = ("https://konachan.com/post/random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="highres").get("href")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def e621(self, ctx):
        """Random Image From e621"""
        try:
            query = ("https://e621.net/post/random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="highres").get("href")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def rule34(self, ctx):
        """Random Image From rule34"""
        try:
            query = ("http://rule34.xxx/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send('http:' + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def danbooru(self, ctx):
        """Random Image From Danbooru"""
        try:
            query = ("http://danbooru.donmai.us/posts/random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send('http://danbooru.donmai.us' + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def gelbooru(self, ctx):
        """Random Image From Gelbooru"""
        try:
            query = ("http://www.gelbooru.com/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def tbib(self, ctx):
        """Random Image From DrunkenPumken"""
        try:
            query = ("http://www.tbib.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send("http:" + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def xbooru(self, ctx):
        """Random Image From Xbooru"""
        try:
            query = ("http://xbooru.com/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def furrybooru(self, ctx):
        """Random Image From Furrybooru"""
        try:
            query = ("http://furry.booru.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def drunkenpumken(self, ctx):
        """Random Image From DrunkenPumken"""
        try:
            query = ("http://drunkenpumken.booru.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(no_pm=True)
    @checks.is_nsfw()
    async def lolibooru(self, nsfw):
        """Random Image From Lolibooru"""
        try:
            query = ("https://lolibooru.moe/post/random/")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            image = image.replace(' ','%20')
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def ysearch(self, ctx, *tags: str):
        """Search Yandere With A Tag"""
        if tags == ():
            await ctx.send(":warning: Tags are missing.")
        else:
            try:
                tags = ("+").join(tags)
                query = ("https://yande.re/post.json?limit=42&tags=" + tags)
                page = await self.session.get(query)
                json = await page.json()
                if json != []:
                    await ctx.send(random.choice(json)['jpeg_url'])
                else:
                    await ctx.send(":warning: Yande.re has no images for requested tags.")
            except Exception as e:
                await ctx.send(":x: `{}`".format(e))

def setup(bot):
    n = Nsfw(bot)
    bot.add_cog(n)