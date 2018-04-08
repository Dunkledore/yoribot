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
import random
from random import randint
from random import choice
import datetime
from datetime import date
import operator
import logging

class Searches:
    """Different search commands - YouTube, Google, random cat, random dog. """
    def __init__(self, bot):
        self.bot = bot
        self.youtube_regex = (
          r'(https?://)?(www\.)?'
          '(youtube|youtu|youtube-nocookie)\.(com|be)/'
          '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        self.url_dog = "https://random.dog/woof.json"
        self.url_cat = "https://aws.random.cat/meow"
        self.numbs = {
            1: "1\U000020E3",
            2: "2\U000020E3",
            3: "3\U000020E3",
            4: "4\U000020E3",
            5: "5\U000020E3",
            6: "6\U000020E3",
            7: "7\U000020E3",
            8: "8\U000020E3",
            9: "9\U000020E3",
        }
        self.catagory = "Personal Utility"

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
        

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url_cat) as response:
                text = await response.text()
                json_text = json.loads(text)
                img = json_text["file"].replace("\\/","/")
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
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url_dog) as response:
                text = await response.text()
                json_text = json.loads(text)
                img = json_text["url"].replace("\\/","/")
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
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "Step 1 - Visit google.com"))
        await asyncio.sleep(2)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title ="Step 2 - Type:", description=text))
        await asyncio.sleep(2)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title ="Step 3 - Click the Button"))
        await asyncio.sleep(2)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title ="That's it!", description=" https://www.google.com/search?q="+query))

    @commands.command()
    async def dadjoke(self,ctx):
        """Gets a random dad joke."""
        api = 'https://icanhazdadjoke.com/'
        async with aiohttp.request('GET', api, headers={'Accept': 'text/plain'}) as r:
            result = await r.text()
            head, sep, tail = result.partition('?'or'.')
            await ctx.send(head+sep)
            await asyncio.sleep(10)
            if tail is None or tail == "":
                return
            else:
                await ctx.send(tail)

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
    async def xmasclock(self,ctx):
        """Display days left 'til xmas"""

        now = datetime.datetime.now()
        today = date(now.year, now.month, now.day)

        year = now.year
        if (now.month == 12 and now.day > 25):
            year = now.year + 1

        xmasday = date(year, 12, 25)

        delta = xmasday - today

        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = str(delta.days) + " days left until Xmas!"))

    @commands.command()
    @commands.guild_only()
    async def whoplays(self, ctx, *, game):
        """Shows a list of all the people playing a game."""
        if len(game) <= 2:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ="You need to enter at least 3 characters for the game name."))
            return

        user = ctx.message.author
        guild = ctx.message.guild
        members = guild.members

        playing_game = ""
        count_playing = 0
        for member in members:
            if not member:
                continue
            if not member.game or not member.game.name:
                continue
            if member.bot:
                continue
            if game.lower() in member.game.name.lower():
                count_playing += 1
                if count_playing <= 15:
                    playing_game += "▸ {} ({})\n".format(member.name,
                                                         member.game.name)

        if playing_game == "":
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ WTF?",
                                description ="No one is playing that game."))
        else:
            msg = playing_game
            em = discord.Embed(description=msg, colour=user.colour)
            if count_playing > 15:
                showing = "(Showing 15/{})".format(count_playing)
            else:
                showing = "({})".format(count_playing)
            text = "These are the people who are playing"
            text += "{}:\n{}".format(game, showing)
            em.set_author(name=text)
            await ctx.send(embed=em)

    @commands.command()
    @commands.guild_only()
    async def cgames(self, ctx):
        """Shows the currently most played games"""
        user = ctx.message.author
        guild = ctx.message.guild
        members = guild.members

        freq_list = {}
        for member in members:
            if not member:
                continue
            if not member.game or not member.game.name:
                continue
            if member.bot:
                continue
            if member.game.name not in freq_list:
                freq_list[member.game.name] = 0
            freq_list[member.game.name] += 1

        sorted_list = sorted(freq_list.items(),
                             key=operator.itemgetter(1),
                             reverse=True)

        if not freq_list:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ WTF?",
                                description ="Surprisingly, no one is playing anything."))
        else:
            # create display
            msg = ""
            max_games = min(len(sorted_list), 10)
            for i in range(max_games):
                game, freq = sorted_list[i]
                msg += "▸ {}: __{}__\n".format(game, freq_list[game])

            em = discord.Embed(description=msg, colour=user.colour)
            em.set_author(name="These are the server's most played games at the moment:")
            await ctx.send(embed=em)

    @commands.command(aliases=['owners'])
    async def gamesales(self, ctx, *, game):
        """Shows estimated amount of owners for the game"""

        # gets info from SteamSpy
        async def gatherGameInfo(appid):

            # get the game info by appid from SteamSpy (c)
            # ratelimited for 4 req/s
            # TODO: add local caching
            url = "http://steamspy.com/api.php?"
            url += "request=appdetails"
            url += "&"
            url += "appid=" + str(appid)

            async with aiohttp.get(url) as r:
                data = await r.json()
            if "error" not in data.keys():
                return data
            else:
                return None

        # result refiner process
        async def refineResults(result):
            # strip all trailers
            trailerR = re.compile('trailer|demo', re.I)
            result = [g for g in result if trailerR.search(g['name']) is None][0:9]

            em = discord.Embed(title="Multiple results",
            description="Please select one by clicking a number below the message",
            colour=0x2F668D)

            lines = []
            for game in enumerate(result[0:9]):
                lines.append("**#{}** - {}".format(game[0] + 1, game[1]['name']))

            em.add_field(name="Games found",
            value='\n'.join(lines),
            inline=False)

            emojis =[]

            message = await ctx.send(embed=em)
            for line in enumerate(lines):
                await self.bot.add_reaction(message, "{}\U000020E3".format(line[0] + 1))
                emojis.append("{}\U000020E3".format(line[0]))

            react = await self.bot.wait_for_reaction(
                message=message, user=ctx.message.author, timeout=15,
                emoji=emojis
            )
            if react is None:
                for line in enumerate(lines):
                    await self.bot.remove_reaction(message, "{}\U000020E3".format(line[0] + 1), self.bot.user)
                return None

            reacts = {v: k for k, v in self.numbs.items()}
            react = reacts[react.reaction.emoji]
            if react:
                await self.bot.delete_message(message)
                return(result[int(react) - 1]['appid'])
            else:
                return None

        # get the appIds list first
        url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"

        # we will store our stuff in here
        result = []
        async with aiohttp.get(url) as r:
            data = await r.json()
        if "error" not in data.keys():

            # check for romanian numbers
            testR = re.compile('\s[vVxX](\W|$)',).search(game)
            if testR is not None:
                game = game[:testR.start() + 1] + '\s' + game[testR.start() + 1:]

            # create regexp for matching
            test = re.compile('.*' + '.*'.join(game.split()) + '.*', re.I)

            # Build the data into a nice table and send
            for d in data['applist']['apps']:
                if test.search(d['name'].lower()) is not None:
                    result.append({
                        "appid": d['appid'],
                        "name": d['name']
                    })

            gameResult = None
            appId = None
            if len(result) == 0:
                # no games were found
                return await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ='There are no games like that one :\'('))
            elif len(result) == 1:
                # only one game matched
                appId = result[0]['appid']
                gameResult = await gatherGameInfo(appId)
            else:
                # multiple matches
                gPos = None
                try:
                    # searches for the exact game name (case-insensitive)
                    gPos = next(i for i, g in enumerate(result) if g['name'].lower() == game.lower())
                except ValueError:
                    gPos = None
                except StopIteration:
                    gPos = None

                if gPos is not None:
                    # if found exact game name in the list of matches
                    appId = result[gPos]['appid']
                    # SteamSpy API
                    apiReturn = await gatherGameInfo(appId)
                    # if SteamSpy returned data
                    if apiReturn is not None:
                        gameResult = apiReturn
                else:
                    # let the user choose from the list of matches
                    appId = await refineResults(result)
                    # SteamSpy API
                    apiReturn = await gatherGameInfo(appId)
                    # if SteamSpy returned data
                    if apiReturn is not None and appId is not None:
                        gameResult = apiReturn

            if gameResult is not None:
                # build embed
                em = discord.Embed(title=gameResult['name'],
                                   url='http://store.steampowered.com/app/' + str(appId),
                                   colour=0x2F668D)
                em.set_thumbnail(url='http://cdn.akamai.steamstatic.com/steam/apps/' + str(appId) + '/header.jpg')
                em.set_author(name='Steam Spy',
                              url='http://steamspy.com/app/' + str(appId),
                              icon_url='https://pbs.twimg.com/profile_images/624266818891423744/opyF6mM5_400x400.png')
                em.add_field(name='Owners',
                             value=str('{0:,}'.format(gameResult['owners'])) + ' ±' + str('{0:,}'.format(gameResult['owners_variance'])),
                             inline=True)
                em.add_field(name='Players in last 2 weeks',
                             value=str('{0:,}'.format(gameResult['players_2weeks'])) + ' ±' + str('{0:,}'.format(gameResult['players_2weeks_variance'])),
                             inline=True)
                em.add_field(name='Peak in 24 hours',
                             value=str('{0:,}'.format(gameResult['ccu'])),
                             inline=True)
                em.set_footer(text='<3 SteamSpy')

                # send embed
                await ctx.send(embed=em)
            # else:
            #     # something went wrong
            #     # await ctx.send('Something went wrong with SteamSpy')
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ='Something went wrong with Steam'))

    @commands.command(name='steam')
    async def steamgame(self, ctx, *, game):
        """Gets the link to a game on Steam"""

        # result refiner process
        async def refineResults(result):
            result = result[0:5]

            message = "Found a lot of results, please choose one (type a number from the list): \n \n"

            for game in enumerate(result):
                message += str(game[0] + 1) + ". " + str(game[1]['name']) + "\n"

            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "Games",
                                description =message))

            # number checker
            def is_number(s):
                try:
                    int(s)
                    return True
                except ValueError:
                    return False
            def check(m):
                return m.author.id == ctx.message.author.id
            answer = await self.bot.wait_for('message',timeout=15, check=check)

            if answer:
                if is_number(answer.content.strip()) and int(answer.content.strip()) in range(1, 6):
                    await ctx.send("http://store.steampowered.com/app/" +
                                       str(result[int(answer.content.strip()) - 1]['appid']))
                else:
                    await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ="Please enter just a number next time :("))

        # get the appIds list first
        url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
        # we will store our stuff in here
        result = []
        async with aiohttp.get(url) as r:
            data = await r.json()
        if "error" not in data.keys():

            # check for romanian numbers
            testR = re.compile('\s[vVxX](\W|$)').search(game)
            if testR is not None:
                game = game[:testR.start() + 1] + '\s' + game[testR.start() + 1:]

            # create regexp for matching
            test = re.compile('.*' + '.*'.join(game.split()) + '.*', re.I)

            # Build the data into a nice table and send
            for d in data['applist']['apps']:
                if test.search(d['name'].lower()) is not None:
                    result.append({
                        "appid": d['appid'],
                        "name": d['name']
                    })
            if len(result) == 0:
                return await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ='There are no games like that one :\'('))
            elif len(result) == 1 or result[0]['name'] == game:
                await ctx.send("http://store.steampowered.com/app/" +
                                   str(result[0]['appid']))
            else:
                await refineResults(result)
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description =data["error"]))

def setup(bot):
    n = Searches(bot)
    bot.add_cog(n)