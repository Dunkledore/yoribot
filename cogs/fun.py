import discord
from discord.ext import commands
from .utils.dataIO import fileIO
from random import choice as randchoice
from random import randint, sample
from random import choice as rnd
from random import choice
from enum import Enum
from urllib.parse import quote_plus
import datetime
from .utils import checks
from .utils.dataIO import dataIO
import aiohttp
import time
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
    rock = "\N{MOYAI}"
    paper = "\N{PAGE FACING UP}"
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
    """
    Various fun and entertaining commands to keep things interesting!
    """

    def __init__(self, bot):
        self.bot = bot
        self.items = fileIO("data/fun/items.json", "load")
        self.thotchoices = fileIO("data/fun/thotchoices.json", "load")
        self.lines = dataIO.load_json("data/fun/lines.json")
        self.ball = ["As I see it, yes", "It is certain", "It is decidedly so", "Most likely", "Outlook good",
                     "Signs point to yes", "Without a doubt", "Yes", "Yes – definitely", "You may rely on it", "Reply hazy, try again",
                     "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
                     "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
        self.toggle = False
        self.feelings = "data/fun/feelings.json"
        self.system = dataIO.load_json(self.feelings)
        self.stopwatches = {}
        self.catagory = "Games"

    def save_emotes(self):
        dataIO.save_json(self.feelings, self.system)
        dataIO.is_valid_json("data/fun/feelings.json")

    @commands.group(invoke_without_command=True, no_pm=True)
    async def fun(self, ctx):
        """Random text commands for creating chaos!
        """
    @fun.command()
    async def riot(self, ctx, *text):
        """RIOT!"""
        text = " ".join(text)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                           title="(ʘ言ʘ╬)  This is a Riot!    (╬ Ò ‸ Ó)",
                                           description=text))

    @fun.command()
    async def thot(self, ctx, user):
        """Determines if a user is a thot or not"""
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                           title="Is {} a thot?".format(
                                               ctx.message.mentions[0].name),
                                           description="{} {}".format(ctx.message.mentions[0].name, randchoice(self.thotchoices))))

    def save_items(self):
        fileIO("data/fun/items.json", 'save', self.items)

    @fun.command(pass_context=True)
    async def roll(self, ctx, number: int = 100):
        """Rolls random number (between 1 and user choice)

        Defaults to 100.
        """
        author = ctx.message.author
        if number > 1:
            n = randint(1, number)
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title=":game_die:",
                                               description="You rolled: {}".format(n)))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="⚠ Error",
                                               description="{} Maybe higher than 1? ;P".format(author.mention)))

    @fun.command()
    async def rps(self, ctx, your_choice: RPSParser):
        """Play rock paper scissors"""
        author = ctx.message.author
        player_choice = your_choice.choice
        red_choice = choice((RPS.rock, RPS.paper, RPS.scissors))
        cond = {
            (RPS.rock,     RPS.paper): False,
            (RPS.rock,     RPS.scissors): True,
            (RPS.paper,    RPS.rock): True,
            (RPS.paper,    RPS.scissors): False,
            (RPS.scissors, RPS.rock): False,
            (RPS.scissors, RPS.paper): True
        }

        if red_choice == player_choice:
            outcome = None  # Tie
        else:
            outcome = cond[(player_choice, red_choice)]

        if outcome is True:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="You win {}!"
                                               "".format(author.mention),
                                               description="Yori picked {}"
                                               "".format(red_choice.value)))
        elif outcome is False:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="You lost {}!"
                                               "".format(author.mention),
                                               description="Yori picked {}"
                                               "".format(red_choice.value)))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="{} it was a tie!"
                                               "".format(author.mention),
                                               description="Yori picked {} too."
                                               "".format(red_choice.value)))

    @fun.command(name="8", aliases=["8ball"])
    async def _8ball(self, ctx, *, question: str):
        """Ask 8 ball a question

        Question must end with a question mark.
        """
        if question.endswith("?") and question != "?":
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="The Magic 8 Ball Says",
                                               description=choice(self.ball)))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="⚠ Error",
                                               description="That doesn't look like a question."))

    @fun.command()
    async def flip(self, ctx, user: discord.Member=None):
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

    @fun.command()
    async def hug(self, ctx, user: discord.Member, intensity: int=1):
        """Because everyone likes hugs

        Up to 10 intensity levels."""
        name = user.nick or user.name
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

    @fun.command()
    async def guard(self, ctx):
        """Says a random guard line from Skyrim"""
        await ctx.send(choice(self.lines))

    @fun.command()
    async def countdown(self, ctx):
        """Count down... 3,2,1, go!"""

        for i in range(3):
            await ctx.send(3 - i)
            await asyncio.sleep(1)

        await ctx.send('go')

    @commands.group(invoke_without_command=True)
    async def slap(self, ctx, user: discord.Member=None):
        """Slap a user"""
        botid = self.bot.user.id
        if user is None:
            user = ctx.message.author
            await ctx.send("Dont make me slap you instead " + user.name)
        elif user.id == botid:
            user = ctx.message.author
            botname = self.bot.user.name
            await ctx.send("-" + botname + " slaps " + ctx, user.mention +
                           " multiple times with " +
                           (randchoice(self.items) + "-"))
        else:
            await ctx.send("-slaps " + (user.nick or user.name) + " with " +
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

    @commands.command()
    async def blame(self, ctx, user: discord.Member):
        """Was totally their fault"""

        embed = discord.Embed(color=ctx.message.author.color, title="Blame this person",
                              description=user.display_name + " ----------> ")
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["sw"])
    async def stopwatch(self, ctx):
        """Starts/stops stopwatch"""
        author = ctx.message.author
        if not str(author.id) in self.stopwatches:
            self.stopwatches[str(author.id)] = int(time.perf_counter())
            await ctx.send(author.mention + " Stopwatch started!")
        else:
            tmp = abs(self.stopwatches[str(author.id)
                                       ] - int(time.perf_counter()))
            tmp = str(datetime.timedelta(seconds=tmp))
            await ctx.send(author.mention + " Stopwatch stopped! Time: **" + tmp + "**")
            self.stopwatches.pop(str(author.id), None)

    @commands.group(aliases=["kao"], invoke_without_command=True)
    async def kaomoji(self, ctx, *, category: str, n: int=None):
        """Send a japanese emoji (the text kind)."""
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
    async def _list(self, ctx):
        """Shows all categories"""
        categories = [i for i in self.system]
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                           title="Kaomoji Categories",
                                           description=', '.join(categories)))
        print("Kaomoji list called")

    @kaomoji.command()
    async def count(self, ctx, category: str):
        """Displays count per category"""
        str_category = category.lower()
        amount = len(self.system[str_category])
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                           title="Kaomoji's Available in " + str_category,
                                           description="There are " + str(amount) + " kaomojis for " + str_category))

    @kaomoji.command()
    async def cleaner(self, ctx, on_off: str):
        """Cleans up your commands"""
        if on_off is True:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description='Deleting commands is now ON.'))
            self.toggle = True
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description='Deleting commands is now OFF.'))
            self.toggle = False

    @commands.group(invoke_without_command=True, no_pm=True)
    async def gif(self, ctx):
        """Random text commands for creating chaos!
        """

    @gif.command(pass_context=True, invoke_without_command=True)
    async def kiss(self, ctx, *, user: discord.Member):
        """Kiss people!"""
        sender = ctx.message.author
        folder = "kiss"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " You pervert! You cannot do that to yourself!")
        else:
            await self.upload_random_gif(ctx, user.mention + " was KISSED by " + sender.mention + "! :kiss:", folder)

    @gif.command()
    async def bite(self, ctx, *, user: discord.Member):
        """Bite people!"""
        sender = ctx.message.author
        folder = "bite"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " As kinky as that is, I can't let you do that to yourself!")
        else:
            await self.upload_random_gif(ctx, user.mention + " was BITTEN by " + sender.mention + "! ", folder)

    @gif.command()
    async def slap(self, ctx, *, user: discord.Member):
        """Slap people!"""
        sender = ctx.message.author
        folder = "slap"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " You Masochist! You cannot do that to yourself!")
        else:
            await self.upload_random_gif(
                ctx, user.mention + " was SLAPPED by " + sender.mention + " and i think they liked it! ", folder)

    @gif.command()
    async def taunt(self, ctx, *, user: discord.Member):
        """Taunt people!"""
        sender = ctx.message.author
        folder = "taunt"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " You must be really lonely? Do you need a friend? ")
        else:
            await self.upload_random_gif(ctx, user.mention + " was TAUNTED by " + sender.mention + "! ", folder)

    @gif.command()
    async def cuddle(self, ctx, *, user: discord.Member):
        """Cuddle people!"""
        sender = ctx.message.author
        folder = "cuddle"
        if ctx.message.author == user:
            await ctx.send(
                sender.mention + " I am sorry that you are so lonely, but you cannot Cuddle with yourself, Thats masterbation! ")
        else:
            await self.upload_random_gif(
                ctx, user.mention + " CUDDLES HARD with " + sender.mention + " , and they like it! ", folder)

    @gif.command()
    async def hugg(self, ctx, *, user: discord.Member):
        """Hug people!"""
        sender = ctx.message.author
        folder = "hug"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " Sorry, you are not that flexible. You cannot Hug yourself!")
        else:
            await self.upload_random_gif(ctx, user.mention + " was given a BIG hug from " + sender.mention + "! ", folder)

    @gif.command()
    async def feed(self, ctx, *, user: discord.Member):
        """Feed people!"""
        sender = ctx.message.author
        folder = "feeds"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " I'm so glad you know how to feed yourself! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " was FED by " + sender.mention + "! ", folder)

    @gif.command()
    async def spank(self, ctx, *, user: discord.Member):
        """Spank people!"""
        sender = ctx.message.author
        folder = "spank"
        if ctx.message.author == user:
            await ctx.send(
                sender.mention + " I NEED AN ADULT!!! You cannot use me to spank yourself. Thats Nasty! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " was SPANKED HARD by " + sender.mention + " , and they LOVED it! ", folder)

    @gif.command()
    async def tease(self, ctx, *, user: discord.Member):
        """Tease people!"""
        sender = ctx.message.author
        folder = "tease"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " You're a special person aren't you? You cannot tease yourself! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " was TEASED by " + sender.mention + "! ", folder)

    @gif.command()
    async def hi5(self, ctx, *, user: discord.Member):
        """HighFive people!"""
        sender = ctx.message.author
        folder = "hi5"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " Nice try, You have to get out more! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " was HIGHFIVED by " + sender.mention + "! ", folder)

    @gif.command()
    async def shoot(self, ctx, *, user: discord.Member):
        """Shoot people!"""
        sender = ctx.message.author
        folder = "shoot"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " Calm down! I am sure we can solve whatever problem you're having. ")
        else:
            await self.upload_random_gif(ctx, user.mention + " was SHOT by " + sender.mention + "! They survived! ", folder)

    @gif.command()
    async def lick(self, ctx, *, user: discord.Member):
        """Lick people!"""
        sender = ctx.message.author
        folder = "lick"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " Well aren't you a kinky little thing? And very flexible! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " was LICKED by " + sender.mention + "! ", folder)

    @gif.command()
    async def shake(self, ctx, *, user: discord.Member):
        """Handshake!"""
        sender = ctx.message.author
        folder = "handshake"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " No, Just No! Get a life! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " Shook " + sender.mention + "'s Hand! ", folder)

    @gif.command()
    async def twerk(self, ctx, *, user: discord.Member):
        """TWERK!"""
        sender = ctx.message.author
        folder = "twerk"
        if ctx.message.author == user:
            await ctx.send(
                sender.mention + " Did you just try to twerk on yourself? We'll pretend that never happened! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " TWERKED FOR " + sender.mention + "! and they LIKED it! ",
                                         folder)

    @gif.command()
    async def strip(self, ctx, *, user: discord.Member):
        """STRIP!"""
        sender = ctx.message.author
        folder = "strip"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " No, Just No! Get a life! ")
        else:
            await self.upload_random_gif(ctx, sender.mention + " strips for " + user.mention + " and they LIKE it! ", folder)

    @gif.command()
    async def thirsty(self, ctx, *, user: discord.Member):
        """The Thirst is Real!"""
        sender = ctx.message.author
        folder = "thirsty"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " Really? Just really?? You need help! ")
        else:
            await self.upload_random_gif(ctx, sender.mention + " tells " + user.mention + " To calm your thirsty ass down! ",
                                         folder)

    @gif.command()
    async def moist(self, ctx, *, user: discord.Member):
        """Moist lol!"""
        sender = ctx.message.author
        folder = "moist"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " You are way to easy! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " has made " + sender.mention + " moist. OH LORD! ", folder)

    @gif.command()
    async def whip(self, ctx, *, user: discord.Member):
        """Whip someone!"""
        sender = ctx.message.author
        folder = "whip"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " Well aren't you just a kinky thing! ")
        else:
            await self.upload_random_gif(ctx, sender.mention + " has whipped " + user.mention + " and i think they LIKED it! ", folder)

    @gif.command()
    async def facepalm(self, ctx, *, user: discord.Member):
        """Facepalm images!"""
        sender = ctx.message.author
        folder = "facepalm"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " You cannot do that to yourself! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " has made " + sender.mention + " FACEPALM! ", folder)

    @gif.command()
    async def ohno(self, ctx, *, user: discord.Member):
        """Oh no they didnt images!"""
        sender = ctx.message.author
        folder = "ono"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " You cannot do that to yourself! ")
        else:
            await self.upload_random_gif(ctx, sender.mention + " yells at " + user.mention + " Oh no they didn't! ", folder)

    @gif.command()
    async def hungry(self, ctx, *, user: discord.Member):
        """Hungry images!"""
        sender = ctx.message.author
        folder = "hungry"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " THEN GO GET SOMETHING TO EAT! ")
        else:
            await self.upload_random_gif(ctx, user.mention + " has made " + sender.mention + " HUNGRY! ", folder)

    @gif.command()
    async def nuts(self, ctx, *, user: discord.Member):
        """NutCracker images!"""
        sender = ctx.message.author
        folder = "nuts"
        if ctx.message.author == user:
            await ctx.send(sender.mention + " No, Just no! Get a life! ")
        else:
            await self.upload_random_gif(ctx, sender.mention + " wants to kick " + user.mention + " in the NUTS! OUCH!! ",
                                         folder)

    @gif.command()
    async def fever(self, ctx):
        """Do you have the Fever?"""
        sender = ctx.message.author
        folder = "fever"
        await self.upload_random_gif(ctx, sender.mention + "I see you have the fever.... The Bieber fever", folder)

    async def upload_random_gif(self, ctx, msg, folder):
        if msg:
            await ctx.send(msg)
        folderPath = "data/fun/" + folder
        fileList = os.listdir(folderPath)
        gifPath = folderPath + "/" + fileList[randint(0, len(fileList) - 1)]
        await ctx.send(file=discord.File(gifPath))


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
