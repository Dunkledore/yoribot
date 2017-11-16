import discord
from discord.ext import commands
from .utils.dataIO import fileIO
from random import choice as randchoice
import os

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
        user = ctx.message.author
        await ctx.send("{} {}".format(user.mention, randchoice(self.thotchoices)))

def setup(bot):
    bot.add_cog(Fun(bot))