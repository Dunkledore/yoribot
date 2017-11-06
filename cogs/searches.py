from discord.ext import commands
import aiohttp
import discord
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
        self.file_path = "data/animelist/credentials.json"
        self.credentials = dataIO.load_json(self.file_path)

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

    @commands.command(pass_context=True, name='anime', no_pm=True)
    async def _anime(self, ctx, *, query: str):
        """Search on My Anime List"""
        try:
            url = 'https://www.animenewsnetwork.com/encyclopedia/search/name?'
            payload = {'search_query': ''.join(query)}
            headers = {'user-agent': 'Red-cog/1.0'}
            conn = aiohttp.TCPConnector(verify_ssl=False)
            session = aiohttp.ClientSession(connector=conn)
            async with session.get(url, params=payload, headers=headers) as r:
                result = await r.text()
            session.close()
            al_find = re.findall(r'href=\"\/name\?q=(.{11})', result)
            url = 'https://www.animenewsnetwork.com/encyclopedia/search/name?q={}'.format(al_find[0])
            await ctx.send(url)
        except Exception as e:
            message = 'Something went terribly wrong! [{}]'.format(e)
            await ctx.send(message)
def setup(bot):
    n = Searches(bot)
    bot.add_cog(n)