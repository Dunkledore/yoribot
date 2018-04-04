import asyncpg
import discord
from discord.ext import commands

from .utils import checks

class Gaming:

    """A warning system with automatic banning and muting """

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command()
    @commands.guild_only()
    async def nowplaying(self, ctx):
        """Will show you who is playing what games in the current guild."""
 

    @commands.command()
    @commands.guild_only()
    async def iplay(self, ctx):
        """Shows the different games you have played."""

    @commands.command()
    @commands.guild_only()
    async def whoplays(self, ctx, *, gamename):
        """Shows who plays the game provided."""

    @commands.command()
    @commands.guild_only()
    async def lfg(self, ctx, *, gamename):
        """Notifies the people who play the provided game that you are looking for group."""

    @commands.command()
    @commands.guild_only()
    async def ign(self, ctx, member: discord.Member, *, gamename):
        """Shows a member's name for the designated game (only works if the user provided the info to the bot)."""

    @commands.command()
    @commands.guild_only()
    async def myign(self, ctx, member: discord.Member, gamename, ign):
        """Add your ign for a designated game."""



def setup(bot: commands.Bot):
    n = Warnings(bot)
    bot.add_cog(n)