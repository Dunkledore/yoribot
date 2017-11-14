from discord.ext import commands
import aiohttp
import discord
import json
import asyncio
import re
import os
import html
from xml.etree import ElementTree as ET
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks


class Searches:
    """Different search commands - YouTube, """
    def __init__(self, bot):
        self.bot = bot
        self.youtube_regex = (
          r'(https?://)?(www\.)?'
          '(youtube|youtu|youtube-nocookie)\.(com|be)/'
          '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        self.url_dog = "https://random.dog/woof.json"
        self.url_cat = "https://random.cat/meow"

    @commands.command(pass_context=True, name='youtube', no_pm=True)
    async def _youtube(self, ctx, *, query: str):
        """Search on Youtube"""
        try:
            url = 'https://www.youtube.com/results?'
            payload = {'search_query': ''.join(query)}
            headers = {'user-agent': 'Red-cog/1.0'}
            conn = aiohttp.TCPConnector(verify_ssl=False)
            session = aiohttp.ClientSession(connector=conn)
            async with session.get(url, params=payload, headers=headers) as r:
                result = await r.text()
            session.close()
            yt_find = re.findall(r'href=\"\/watch\?v=(.{11})', result)
            url = 'https://www.youtube.com/watch?v={}'.format(yt_find[0])
            await ctx.send(url)
        except Exception as e:
            message = 'Something went terribly wrong! [{}]'.format(e)
            await ctx.send(message)

    @commands.command(pass_context=True, no_pm=True)
    async def meow(self, ctx: commands.Context):
        """Gets a random cat picture."""

        async with aiohttp.get(self.url_cat) as response:
            img = json.loads(await response.text())["file"].replace("\\/","/")
            await ctx.send(img)

    @commands.command(pass_context=True, no_pm=True)
    async def woof(self, ctx: commands.Context):
        """Gets a random dog picture."""

        async with aiohttp.get(self.url_dog) as response:
            img = json.loads(await response.text())["url"]
            await ctx.send(img)

    @commands.command()
    async def lmgtfy(self, ctx, *text):
        """Let me just Google that for you..."""

        #Your code will go here
        text = " ".join(text)
        query=text.replace(" ", "%20")
        await ctx.send("Step 1 - Visit google.com")
        await asyncio.sleep(2)
        await ctx.send("Step 2 - Type \""+ text +"\"")
        await asyncio.sleep(2)
        await ctx.send("Step 3 - Click the Button")
        await asyncio.sleep(2)
        await ctx.send("That's it! https://www.google.com/search?q="+query)

def setup(bot):
    n = Searches(bot)
    bot.add_cog(n)