# Developed by Redjumpman for Twentysix26's Redbot.
# Ported from mee6bot to work for Red
# Original credit and design goes to mee6
import aiohttp
import html
import os
import random
import re
from xml.etree import ElementTree as ET

import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks

# Username and Password is obtained from myanime list website
# You need to create an account there and input the information below

switcher = ['english', 'score', 'type', 'episodes', 'volumes', 'chapters', 'status', 'type',
            'start_date', 'end_date']


class AnimeList:
    """Fetch info about an anime title"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/animelist/credentials.json"
        self.credentials = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def animeset(self, ctx):
        """Sets your username and password from myanimelist"""
        await self.owner_set(ctx)

    @commands.command(pass_context=True, no_pm=True)
    async def anime(self, ctx, *, title):
        """Shows MAL information on an anime"""
        cmd = "anime"
        await self.search_command(ctx, cmd, title)

    @commands.command(pass_context=True, no_pm=True)
    async def manga(self, ctx, *, title):
        """Shows MAL information on a manga"""
        cmd = "manga"
        await self.search_command(ctx, cmd, title)

    async def search_command(self, ctx, cmd, title):
        if self.verify_credentials():
            await self.fetch_info(ctx, cmd, title)
        else:
            await ctx.send("The bot owner has not setup their credentials. "
                               "An account on <https://myanimelist.net> is required. "
                               "When the owner is ready, setup this cog with {}animeset "
                               "to enter the credentials".format(ctx.prefix))
    async def owner_set(self, ctx):
        
        def check(m):
            return m.author.id == ctx.message.author.id

        await ctx.author.send("Type your user name. You can reply in this private msg")
        username = await self.bot.wait_for('message', timeout=30.0, check=check)

        if username is None:
            return await ctx.author.send("Username and Password setup timed out.")

        await ctx.author.send("Ok thanks. Now what is your password?")
        password = await self.bot.wait_for('message', timeout=30.0, check=check)

        if password is None:
            return await ctx.author.send("Username and Password setup timed out.")

        if await self.credential_verfication(username.content, password.content, ctx.author):
            self.credentials["Password"] = password.content
            self.credentials["Username"] = username.content
            dataIO.save_json(self.file_path, self.credentials)
            await ctx.author.send("Setup complete. Account details added.\nTry searching for "
                                   "an anime using {}anime".format(ctx.prefix))
            return

    async def credential_verfication(self, username, password, author):
        auth = aiohttp.BasicAuth(login=username, password=password)
        url = "https://myanimelist.net/api/account/verify_credentials.xml"
        with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url) as response:
                status = response.status

                if status == 200:
                    return True

                if status == 401:
                    await author.send("Username and Password is incorrect.")
                    return False

                if status == 403:
                    await author.send("Too many failed login attempts. Try putting in the"
                                       "correct credentials after some time has passed.")
                    return False

    async def fetch_info(self, ctx, cmd, title):
        data = await self.get_xml(cmd, title)

        try:
            root = ET.fromstring(data)

        except ET.ParseError:
            return await ctx.send("I couldn't find anything!")

        else:
            if len(root) == 1:
                entry = root[0]
            else:
                msg = "**Please choose one by giving its number.**\n"
                msg += "\n".join(['{} - {}'.format(n + 1, entry[1].text)
                                  for n, entry in enumerate(root) if n < 10])

                await ctx.send(msg)
                def check(m):
                
                    return m.content.isdigit() and int(m.content) in range(1, len(root) + 1) and ctx.author.id == m.author.id

                try:
                    resp = await self.bot.wait_for('message', timeout=15, check=check)
                except:
                    return
                if resp is None:
                    return

                entry = root[int(resp.content)-1]

            link = 'http://myanimelist.net/{}/{}'.format(cmd, entry.find('id').text)
            desc = "MAL [{}]({})".format(entry.find('title').text, link)
            syn_raw = entry.find('synopsis').text
            title = entry.find('title').text
            if syn_raw:
                replace = {'&quot;': '\"', '<br />': '', '&mdash;': ' - ', '&#039;': '\'',
                           '&ldquo;': '\"', '&rdquo;': '\"', '[i]': '*', '[/i]': '*', '[b]': '**',
                           '[/b]': '**', '[url=': '', ']': ' - ', '[/url]': ''}
                rep_sorted = sorted(replace, key=lambda s: len(s[0]), reverse=True)
                rep_escaped = [re.escape(replacement) for replacement in rep_sorted]
                pattern = re.compile("|".join(rep_escaped), re.I)
                synopsis = pattern.sub(lambda match: replace[match.group(0)],
                                       entry.find('synopsis').text)
            else:
                synopsis = "There is not a synopsis for {}".format(title)

            # Build Embed
            embed = discord.Embed(colour=0x0066FF, description=desc)
            embed.title = title
            embed.set_thumbnail(url=entry.find('image').text)
            embed.set_footer(text=synopsis)

            for k in switcher:
                spec = entry.find(k)
                if spec is not None and spec.text is not None:
                    embed.add_field(name=k.capitalize(),
                                    value=html.unescape(spec.text.replace('<br />', '')))

            await ctx.send(embed=embed)

    async def get_xml(self, nature, name):
        username = self.credentials["Username"]
        password = self.credentials["Password"]
        name = name.replace(" ", "_")
        auth = aiohttp.BasicAuth(login=username, password=password)
        url = 'https://myanimelist.net/api/{}/search.xml?q={}'.format(nature, name)
        with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url) as response:
                data = await response.text()
                return data

    def verify_credentials(self):
        username = self.credentials["Username"]
        password = self.credentials["Password"]
        if username == '' or password == '':
            return False
        else:
            return True


def check_folders():
    if not os.path.exists("data/animelist"):
        print("Creating data/animelist folder...")
        os.makedirs("data/animelist")


def check_files():
    system = {"Username": "",
              "Password": ""}

    f = "data/animelist/credentials.json"
    if not dataIO.is_valid_json(f):
        print("Adding animelist credentials.json...")
        dataIO.save_json(f, system)


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(AnimeList(bot))
