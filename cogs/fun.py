import discord
from discord.ext import commands
from .utils.dataIO import fileIO
from random import choice as randchoice
from random import randint
from random import choice as rnd
from random import choice
from enum import Enum
from urllib.parse import quote_plus
import datetime
from .utils import checks
from .utils.dataIO import dataIO
import aiohttp
import asyncio
import asyncpg
import os

defaults = [
    "Dunkledore's Floppy Disk",
    "Seneth's Hentai Collection",
    "A Nuke",
    "A Loaf Of Bread",
    "My Hand",
    "Granola's wet fish"]

class RPS(Enum):
    rock     = "\N{MOYAI}"
    paper    = "\N{PAGE FACING UP}"
    scissors = "\N{BLACK SCISSORS}"


class RPSParser:
    def __init__(self, argument):
        argument = argument.lower()
        if argument == "rock":
            self.choice = RPS.rock
        elif argument == "paper":
            self.choice = RPS.paper
        elif argument == "scissors":
            self.choice = RPS.scissors
        else:
            raise

class Fun:

    def __init__(self, bot):
        self.bot = bot
        self.items = fileIO("data/fun/items.json", "load")
        self.thotchoices = fileIO("data/fun/thotchoices.json","load")
        self.lines = dataIO.load_json("data/fun/lines.json")
        self.ball = ["As I see it, yes", "It is certain", "It is decidedly so", "Most likely", "Outlook good",
                     "Signs point to yes", "Without a doubt", "Yes", "Yes – definitely", "You may rely on it", "Reply hazy, try again",
                     "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
                     "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
        self.toggle = False
        self.feelings = "data/fun/feelings.json"
        self.system = dataIO.load_json(self.feelings)

    def save_emotes(self):
        dataIO.save_json(self.feelings, self.system)
        dataIO.is_valid_json("data/fun/feelings.json")

    @commands.command(pass_context=True, no_pm=True)
    async def riot(self, ctx, *text):
        """RIOT!"""
        text = " ".join(text)
        await ctx.send('ヽ༼ຈل͜ຈ༽ﾉ **' + text + '** ヽ༼ຈل͜ຈ༽ﾉ')
    
    @commands.command(pass_context=True, no_pm=True)
    async def thot(self, ctx, user):
        """Determines if a user is a thot or not"""
        await ctx.send("{} {}".format(ctx.message.mentions[0].name, randchoice(self.thotchoices)))
    def save_items(self):
        fileIO("data/fun/items.json", 'save', self.items)

    @commands.group(pass_context=True, invoke_without_command=True)
    async def slap(self, ctx, user: discord.Member=None):
        """Slap a user"""
        botid = self.bot.user.id
        if user is None:
            user = ctx.message.author
            await ctx.send("Dont make me slap you instead " + user.name)
        elif user.id == botid:
            user = ctx.message.author
            botname = self.bot.user.name
            await ctx.send("-" + botname + " slaps " + user.mention +
                               " multiple times with " +
                               (randchoice(self.items) + "-"))
        else:
            await ctx.send("-slaps " + user.nick or user.name + " with " +
                               (randchoice(self.items) + "-"))

    @slap.command()
    async def add(self, ctx, item):
        """Adds an item"""
        if item in self.items:
            await ctx.send("That is already an item.")
        else:
            self.items.append(item)
            self.save_items()
            await ctx.send("Item added.")

    @slap.command()
    @checks.is_owner()
    async def remove(self, ctx, item):
        """Removes item"""
        if item not in self.items:
            await ctx.send("That is not an item")
        else:
            self.items.remove(item)
            self.save_items()
            await ctx.send("item removed.")
    @commands.command(pass_context=True)
    async def roll(self, ctx, number : int = 100):
        """Rolls random number (between 1 and user choice)

        Defaults to 100.
        """
        author = ctx.message.author
        if number > 1:
            n = randint(1, number)
            await ctx.send("{} :game_die: {} :game_die:".format(author.mention, n))
        else:
            await ctx.send("{} Maybe higher than 1? ;P".format(author.mention))

    @commands.command(pass_context=True)
    async def flip(self, ctx, user : discord.Member=None):
        """Flips a coin... or a user.

        Defaults to coin.
        """
        if user != None:
            msg = ""
            if user.id == self.bot.user.id:
                user = ctx.message.author
                msg = "Nice try. You think this is funny? How about *this* instead:\n\n"
            char = "abcdefghijklmnopqrstuvwxyz"
            tran = "ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz"
            table = str.maketrans(char, tran)
            name = user.display_name.translate(table)
            char = char.upper()
            tran = "∀qƆpƎℲפHIſʞ˥WNOԀQᴚS┴∩ΛMX⅄Z"
            table = str.maketrans(char, tran)
            name = name.translate(table)
            await ctx.send(msg + "(╯°□°）╯︵ " + name[::-1])
        else:
            await ctx.send("*flips a coin and... " + choice(["HEADS!*", "TAILS!*"]))

    @commands.command(pass_context=True)
    async def rps(self, ctx, your_choice : RPSParser):
        """Play rock paper scissors"""
        author = ctx.message.author
        player_choice = your_choice.choice
        red_choice = choice((RPS.rock, RPS.paper, RPS.scissors))
        cond = {
                (RPS.rock,     RPS.paper)    : False,
                (RPS.rock,     RPS.scissors) : True,
                (RPS.paper,    RPS.rock)     : True,
                (RPS.paper,    RPS.scissors) : False,
                (RPS.scissors, RPS.rock)     : False,
                (RPS.scissors, RPS.paper)    : True
               }

        if red_choice == player_choice:
            outcome = None # Tie
        else:
            outcome = cond[(player_choice, red_choice)]

        if outcome is True:
            await ctx.send("{} You win {}!"
                               "".format(red_choice.value, author.mention))
        elif outcome is False:
            await ctx.send("{} You lose {}!"
                               "".format(red_choice.value, author.mention))
        else:
            await ctx.send("{} We're square {}!"
                               "".format(red_choice.value, author.mention))

    @commands.command(pass_context=True, name="8", aliases=["8ball"])
    async def _8ball(self, ctx, *, question : str):
        """Ask 8 ball a question

        Question must end with a question mark.
        """
        if question.endswith("?") and question != "?":
            await ctx.send("`" + choice(self.ball) + "`")
        else:
            await ctx.send("That doesn't look like a question.")

    @commands.command(aliases=["sw"], pass_context=True)
    async def stopwatch(self, ctx):
        """Starts/stops stopwatch"""
        author = ctx.message.author
        if not author.id in self.stopwatches:
            self.stopwatches[author.id] = int(time.perf_counter())
            await ctx.send(author.mention + " Stopwatch started!")
        else:
            tmp = abs(self.stopwatches[author.id] - int(time.perf_counter()))
            tmp = str(datetime.timedelta(seconds=tmp))
            await ctx.send(author.mention + " Stopwatch stopped! Time: **" + tmp + "**")
            self.stopwatches.pop(author.id, None)

    @commands.command(no_pm=True, hidden=True)
    async def hug(self, user : discord.Member, intensity : int=1):
        """Because everyone likes hugs

        Up to 10 intensity levels."""
        name = italics(user.display_name)
        if intensity <= 0:
            msg = "(っ˘̩╭╮˘̩)っ" + name
        elif intensity <= 3:
            msg = "(っ´▽｀)っ" + name
        elif intensity <= 6:
            msg = "╰(*´︶`*)╯" + name
        elif intensity <= 9:
            msg = "(つ≧▽≦)つ" + name
        elif intensity >= 10:
            msg = "(づ￣ ³￣)づ{} ⊂(´・ω・｀⊂)".format(name)
        await ctx.send(msg)

    @commands.command()
    async def dadjoke(self,ctx):
        """Gets a random dad joke."""
        api = 'https://icanhazdadjoke.com/'
        async with aiohttp.request('GET', api, headers={'Accept': 'text/plain'}) as r:
            result = await r.text()
            head, sep, tail = result.partition('?'or'.')
            await ctx.send(head+sep)
            await asyncio.sleep(10)
            if tail is None:
                return
            else:
                await ctx.send(tail)
    @commands.command()
    async def guard(self,ctx):
        """Says a random guard line from Skyrim"""
        await ctx.send(choice(self.lines))
    @commands.group(aliases=["kao"], invoke_without_command=True, pass_context=True)
    async def kaomoji(self, ctx, *, category: str, n: int=None):
        str_category = category.lower()
        m = ctx.message
        amount = len(self.system.get(str_category, []))
        if str_category in self.system:
            if n is None:
                await ctx.send(rnd(self.system[str_category]))
            else:
                if n > amount:
                    await ctx.send("The highest kaomoji count for " + str_category + " is "
                                       + str(amount) + ". \n(╯°□°）╯︵ ┻━┻")
                else:
                    await ctx.send(self.system[str_category][n])
            print(str_category + " kaomoji called")
        else:
            await ctx.send(str_category + " category couldn't be found. \n¯\_(ツ)_/¯")
        if self.toggle is True:
            try:
                await self.bot.delete_message(m)
                await ctx.send("Deleted command msg {}".format(m.id))
            except discord.errors.Forbidden:
                await ctx.send("Wanted to delete mid {} but no permissions".format(m.id))

    @kaomoji.command(name="list")
    async def _list(self,ctx):
        """Shows all categories"""
        categories = [i for i in self.system]
        await ctx.send("```" + ', '.join(categories) + "```")
        print("Kaomoji list called")

    @kaomoji.command()
    async def count(self, ctx, category: str):
        """Displays count per category"""
        str_category = category.lower()
        amount = len(self.system[str_category])
        await ctx.send("There are " + str(amount) + " kaomojis for " + str_category)

    @kaomoji.command()
    async def cleaner(self, ctx, on_off: str):
        """Cleans up your commands"""
        if on_off is True:
            await ctx.send('Deleting commands is now ON.')
            self.toggle = True
        else:
            await ctx.send('Deleting commands is now OFF.')
            self.toggle = False



def check_folders():
    if not os.path.exists("data/fun"):
        print("Creating data/slap folder...")
        os.makedirs("data/fun")

def check_files():
    f = "data/fun/items.json"
    if not fileIO(f, "check"):
        print("Creating empty items.json...")
        fileIO(f, "save", defaults)
    if not os.path.isfile("data/fun/lines.json"):
        raise RuntimeError(
            "Required data is missing. Please reinstall this cog.")
    if not os.path.isfile("data/fun/feelings.json"):
        raise RuntimeError(
            "Required data is missing. Please reinstall this cog.")

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Fun(bot))