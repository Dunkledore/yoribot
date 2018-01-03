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
import aiohttp
import json
import random
from random import randint
from random import choice
import datetime
from datetime import date

class Searches:
    """Different search commands - YouTube, Google, random cat, random dog. """
    def __init__(self, bot):
        self.bot = bot
        self.youtube_regex = (
          r'(https?://)?(www\.)?'
          '(youtube|youtu|youtube-nocookie)\.(com|be)/'
          '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        self.url_dog = "https://random.dog/woof.json"
        self.url_cat = "https://random.cat/meow"

    @commands.command(name='youtube')
    @commands.guild_only()
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

    @commands.command()
    @commands.guild_only()
    async def meow(self, ctx :commands.Context):
        """Gets a random cat picture."""
        await self.get_meow(ctx)

    async def get_meow(self, ctx: commands.Context):
        

        async with aiohttp.get(self.url_cat) as response:
            img = json.loads(await response.text())["file"].replace("\\/","/")
            if img.endswith(".mp4"):
                await self.get_meow(ctx)
                return

            em = discord.Embed(color=ctx.message.author.color, description=" ")
            em.set_author(name="Random cat picture", icon_url="http://bit.ly/2AH8Byg")
            em.set_image(url=img)
            em.set_footer(text= "Random cat image from https://random.cat")
            await ctx.send(embed=em)

    @commands.command()
    @commands.guild_only()
    async def woof(self, ctx:commands.Context):
        """Gets a random dog picture."""
        await self.get_woof(ctx)

    async def get_woof(self, ctx: commands.Context):
        
        async with aiohttp.get(self.url_dog) as response:
            img = json.loads(await response.text())["url"]
            if img.endswith(".mp4"):
                await self.get_woof(ctx)
                return
                
            em = discord.Embed(color=ctx.message.author.color, description=" ")
            em.set_author(name="Random dog picture", icon_url="http://bit.ly/2jotVFo")
            em.set_image(url=img)
            em.set_footer(text= "Random dog image from https://random.dog")
            await ctx.send(embed=em)

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
    
    @commands.command()
    @commands.guild_only()
    async def fortune(self, ctx):
        """What is your fortune? Well then, lets find out..."""
        
        user = ctx.message.author
        page = randint(1,6)
        link = "http://fortunecookieapi.herokuapp.com/v1/fortunes?limit=&skip=&page={}".format(page)
        async with aiohttp.get(link) as m:
            result = await m.json()
            message = choice(result)
            fortune = discord.Embed(colour=user.colour)
            fortune.add_field(name="{}'s Fortune!".format(user.display_name),value="{}".format(message["message"]))
            await ctx.send(embed=fortune)

    @commands.command()
    async def typeracer(self, ctx, user: str):
        """Get user stats from typeracer"""
        api = 'http://data.typeracer.com/users?id=tr:{}'.format(user)
        async with aiohttp.request("GET", api) as r:
            if r.status == 200:
                result = await r.json()

                random_colour = int("0x%06x" % random.randint(0, 0xFFFFFF), 16)

                last_scores = '\n'.join(str(int(x)) for x in result['tstats']['recentScores'])

                embed = discord.Embed(colour=random_colour, description= " ", url='http://play.typeracer.com/')
                embed.set_author(name=result['name'])
                embed.add_field(name='Country', value=':flag_{}:'.format(result['country']))
                embed.add_field(name='Level', value=result['tstats']['level'])
                embed.add_field(name='Wins', value=result['tstats']['gamesWon'])
                embed.add_field(name='Recent WPM', value=str(result['tstats']['recentAvgWpm']))
                embed.add_field(name='Average WPM', value=str(result['tstats']['wpm']))
                embed.add_field(name='Best WPM', value=str(result['tstats']['bestGameWpm']))
                embed.add_field(name='Recent scores', value=last_scores)
                embed.set_footer(text='typeracer.com')
                await ctx.send(embed=embed)
            else:
                await ctx.send('`Unable to retieve stats for user {}`'.format(user))

    @commands.command()
    async def xmasclock(self,ctx):
        """Display days left 'til xmas"""

        now = datetime.datetime.now()
        today = date(now.year, now.month, now.day)

        year = now.year
        if (now.month == 12 and now.day > 25):
            year = now.year + 1

        xmasday = date(year, 12, 25)

        delta = xmasday - today

        await ctx.send("```" + str(delta.days) + " days left until Xmas!```")

def setup(bot):
    n = Searches(bot)
    bot.add_cog(n)