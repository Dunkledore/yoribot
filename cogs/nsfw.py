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


    @commands.command(pass_context=True)
    @checks.is_nsfw()
    async def dick(self, ctx, user):
        """Show's the size of the user's dick (157% accurate)"""

        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 15)
        y = "=" *  x
        await ctx.send("{}\'s dick:' ** 8{}D **".format(ctx.message.mentions[0].name, y))

    @commands.command(pass_context=True)
    @checks.is_nsfw()
    async def boobs(self, ctx, user):
        """Shows the size of the user's boobs (157% accurate)"""

        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 5)
        y = " " *  x
        await ctx.send("{}\'s boobs:' ** ( .{}Y{}. ) **".format(ctx.message.mentions[0].name, y, y))

    @commands.command(pass_context=True)
    @checks.is_nsfw()
    async def ass(self, ctx, user):
        """Shows the size of the user's ass (157% accurate)"""

        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 5)
        y = " " *  x
        await ctx.send("{}\'s ass:' ** ({}!{}) **".format(ctx.message.mentions[0].name, y, y))

    @commands.command(pass_context=True, no_pm=True)
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

    @commands.command(pass_context=True, no_pm=True)
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

    @commands.command(pass_context=True, no_pm=True)
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

    @commands.command(pass_context=True, no_pm=True)
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

    @commands.command(pass_context=True, no_pm=True)
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

    @commands.command(pass_context=True, no_pm=True)
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

    @commands.command(pass_context=True, no_pm=True)
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
            em = discord.Embed(color=ctx.message.author.color, description=" ")
            em.set_author(name="Random Image from Furrybooru:", icon_url="http://bit.ly/2hHIfF6")
            em.set_image(url=clean)
            em.set_footer(text= "Random image from http://furry.booru.org")
            await ctx.send(embed=em)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command(pass_context=True, no_pm=True)
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
            em = discord.Embed(color=ctx.message.author.color, description=" ")
            em.set_author(name="Random Image from DrunkenPumken:", icon_url="http://bit.ly/2hHIfF6")
            em.set_image(url=clean)
            em.set_footer(text= "Random image from http://drunkenpumken.booru.org")
            await ctx.send(embed=em)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command(pass_context=True, no_pm=True)
    @checks.is_nsfw()
    async def gayorzea(self, ctx):
        """Random Image From Gayorzea"""
        try:
            query = ("http://gayorzea.com/?random")
            page = await self.session.get(query)
            page = await page.text()
            await ctx.send(page)
            soup = BeautifulSoup(page,'html.parser')
            findimage = soup.find("div",{"id" : "image-viewer-container"}).find("img")
            image = await findimage.json()
            if image != []:
                em = discord.Embed(color=ctx.message.author.color, description=" ")
                em.set_author(name="Random Image from Gayorzea:", icon_url="http://bit.ly/2hHIfF6")
                em.set_image(url=random.choice(image)['jpeg_url'])
                em.set_footer(text= "Random image from http://gayorzea.com")
                await ctx.send(embed=em)
            else:
                await ctx.send(":warning: Gayorzea returned no results")
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command(pass_context=True, no_pm=True)
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
                    em = discord.Embed(color=ctx.message.author.color, description=" ")
                    em.set_author(name="Yandere image search:", icon_url="http://bit.ly/2hHIfF6")
                    em.set_image(url=random.choice(json)['jpeg_url'])
                    em.set_footer(text= "Image of"+ tags +"from https://yande.re/")
                    await ctx.send(embed=em)
                else:
                    await ctx.send(":warning: Yande.re has no images for requested tags.")
            except Exception as e:
                await ctx.send(":x: `{}`".format(e))


def setup(bot):
    n = Nsfw(bot)
    bot.add_cog(n)