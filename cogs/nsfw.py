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

    @commands.command(pass_context=True)
    async def penis(self, ctx, user):
        """Rates users sparkliness. 157% accurate!"""

        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 10)
        y = "=" *  x
        await ctx.send("{}\'s dick:' ** 8{}D ** \n {}".format(ctx.message.mentions[0].name, x, y))

    @nsfw.command(pass_context=True, no_pm=True)
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

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def konachan(self, ctx):
        """Random Image From Konachan"""
        try:
            query = ("https://konachan.com/post/random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="highres").get("href")
            await ctx.send('https:' + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def rule34(self, ctx):
        """Random Image From rule34"""
        try:
            query = ("https://rule34.xxx/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send('http:' + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def gelbooru(self, ctx):
        """Random Image From Gelbooru"""
        try:
            query = ("https://www.gelbooru.com/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def tbib(self, ctx):
        """Random Image From DrunkenPumken"""
        try:
            query = ("https://www.tbib.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send("http:" + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def xbooru(self, ctx):
        """Random Image From Xbooru"""
        try:
            query = ("https://xbooru.com/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def furrybooru(self, ctx):
        """Random Image From Furrybooru"""
        try:
            query = ("http://furry.booru.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            head, sep, tail = image.partition('?')
            clean = head.replace("//","/").replace("http:/", "http://")
            await ctx.send(clean)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @nsfw.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def drunkenpumken(self, ctx):
        """Random Image From DrunkenPumken"""
        try:
            query = ("http://drunkenpumken.booru.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            head, sep, tail = image.partition('?')
            clean = head.replace("//","/").replace("http:/", "http://")
            await ctx.send(clean)
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