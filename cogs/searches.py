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

    @commands.command(pass_context=True)
    @checks.admin_or_permissions()
    async def animeset(self, ctx):
        """Sets your username and password from myanimelist"""
        await ctx.author.send("Type your user name. You can reply in this private msg")
        username = await self.bot.wait_for(timeout=15, author=ctx.message.author)
        if username is None:
            return
        else:
            self.credentials["Username"] = username.content
            dataIO.save_json(self.file_path, self.credentials)
            await ctx.author.send("Ok thanks. Now what is your password?")
            password = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)
            if password is None:
                return
            else:
                self.credentials["Password"] = password.content
                dataIO.save_json(self.file_path, self.credentials)
                await ctx.author.send("Setup complete. Account details added.\nTry searching for "
                                       "an anime using {}anime".format(ctx.prefix))

    @commands.command(pass_context=True, no_pm=True)
    async def anime(self, ctx, *, title):
        """Fetches info about an anime title!"""
        cmd = "anime"
        await self.fetch_info(ctx, cmd, title)

    @commands.command(pass_context=True, no_pm=True)
    async def manga(self, ctx, *, title):
        """Fetches info about an manga title!"""
        cmd = "manga"
        await self.fetch_info(ctx, cmd, title)

    async def fetch_info(self, ctx, cmd, title):
        data = await self.get_xml(cmd, title)

        if data == '':
            await ctx.send("I couldn't find anything!")
            return
        try:
            root = ET.fromstring(data)
            if len(root) == 0:
                await ctx.send("I couldn't find anything!")
            elif len(root) == 1:
                entry = root[0]
            else:
                msg = "**Please choose one by giving its number.**\n"
                msg += "\n".join(['{} - {}'.format(n+1, entry[1].text)
                                  for n, entry in enumerate(root) if n < 10
                                  ])

                await ctx.send(msg)

                check = lambda m: m.content in map(str, range(1, len(root)+1))
                resp = await ctx.bot.wait_for(timeout=15, author=ctx.message.author,
                                                       check=check)
                if resp is None:
                    return

                entry = root[int(resp.content)-1]

            link = 'http://myanimelist.net/{}/{}'.format(cmd, entry.find('id').text)
            embed = discord.Embed(colour=0x0066FF,
                                  description=("All the information you need about "
                                               "[{}]({})".format(entry.find('title').text, link)))
            embed.title = entry.find('title').text
            embed.set_thumbnail(url=entry.find('image').text)
            embed.set_footer(text=entry.find('synopsis').text)
            for k in switcher:
                spec = entry.find(k)
                if spec is not None and spec.text is not None:
                    embed.add_field(name=k.capitalize(),
                                    value=html.unescape(spec.text.replace('<br />', '')))

            await ctx.send(embed=embed)
        except:
            await ctx.send("Your username or password is not correct. You need to create an "
                               "account on myanimelist.net.\nIf you have an account use "
                               "**{}animeset** to set your credentials".format(ctx.prefix))

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
    n = Searches(bot)
    check_folders()
    check_files()
    bot.add_cog(n)