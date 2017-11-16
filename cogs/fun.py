import discord
from discord.ext import commands
from .utils.dataIO import fileIO
from random import choice as randchoice
import os

defaults = [
    "Twentysix's Floppy Disk",
    "Eslyium's Hentai Collection",
    "A Nuke",
    "A Loaf Of Bread",
    "My Hand",
    "Will's SquidBot",
    "JennJenn's Penguin Army",
    "Red's Transistor",
    "Asu\u10e6's Wrath",
    "Irdumb's Cookie jar"]

class Fun:

    def __init__(self, bot):
        self.bot = bot
        self.thotchoices = fileIO("data/fun/thotchoices.json","load")

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
    async def slap(self, ctx, *, user: discord.Member=None):
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
                               (rndchoice(self.items) + "-"))
        else:
            await ctx.send("-slaps " + user.name + " with " +
                               (rndchoice(self.items) + "-"))

    @slap.command()
    async def add(self, item):
        """Adds an item"""
        if item in self.items:
            await ctx.send("That is already an item.")
        else:
            self.items.append(item)
            self.save_items()
            await ctx.send("Item added.")

    @slap.command()
    @checks.is_owner()
    async def remove(self, item):
        """Removes item"""
        if item not in self.items:
            await ctx.send("That is not an item")
        else:
            self.items.remove(item)
            self.save_items()
            await ctx.send("item removed.")


def check_folders():
    if not os.path.exists("data/fun"):
        print("Creating data/slap folder...")
        os.makedirs("data/fun")


def check_files():
    f = "data/fun/items.json"
    if not fileIO(f, "check"):
        print("Creating empty items.json...")
        fileIO(f, "save", defaults)

def setup(bot):
    bot.add_cog(Fun(bot))