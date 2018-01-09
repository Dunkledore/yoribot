from discord.ext import commands
import discord
import asyncio
import json
from .utils import db, checks


def embedHR(colour="green", description="", footer=""):
    colours = {"red": discord.Colour.red(), "green": discord.Colour.green(), "yellow": discord.Colour.gold()}
    em = discord.Embed(color=colours[colour], description=description)
    em.set_footer(text=footer)
    em.set_author(name="Hidden Role Helper", icon_url="http://yoribot.com/wp-content/uploads/2017/11/yoriicon.png")
    return em


class Hiddenroles:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._db = {}

    async def _getdata(self, ctx, server=None):
        if server is None:
            query = "SELECT * FROM hiddenroles"
            results = await ctx.db.fetch(query)
            self.bot.get_channel(381089525880979467).send(str(results))

    @commands.group()
    @commands.guild_only()
    @checks.is_mod()
    async def hiddenrole(self, ctx):
        prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]
        em = embedHR("yellow", "This command group is used for management of hidden roles.\n"+prefix)
        await ctx.send(embed=em)

    @hiddenrole.command(name="create")
    @commands.guild_only()
    @checks.is_admin()
    async def create_hiddenrole(self):
        pass

    @hiddenrole.command(name="test")
    @checks.is_developer()
    async def testing(self, ctx):
        await self._getdata(ctx)


def setup(bot):
    bot.add_cog(Hiddenroles(bot))