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
        self.permdata = {}

    async def _getdata(self, ctx, server=None):
        if server is None:
            query = "SELECT * FROM hiddenroles"
            results = await ctx.db.fetch(query)
            await self.bot.get_channel(381089525880979467).send(str(results))
            for r in results:
                self.permdata[r["guild_id"]] = r["permission_data"]
        await self.bot.get_channel(381089525880979467).send(str(self.permdata))


    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.is_mod()
    async def hiddenrole(self, ctx):
        prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]
        em = embedHR("yellow", "This command group is used for management of hidden roles.\n"+prefix)
        await ctx.send(embed=em)

    @hiddenrole.command(name="create")
    @commands.guild_only()
    @checks.is_admin()
    async def create_hiddenrole(self, ctx, name):
        guildid = str(ctx.guild.id)
        if guildid in self.permdata and name in self.permdata[guildid]:
            em = embedHR("red", "This hidden role already exists.")
            await ctx.send(embed=em)
            return
        if guildid not in self.permdata:
            self.permdata[guildid] = {}
            query = "INSERT INTO hiddenroles (guild_id, permission_data) VALUES ($1, $2)"
        else:
            query = "UPDATE hiddenroles SET permission_data = $2 WHERE guild_id = $1"
        self.permdata[guildid][name] = {"deny": [], "allow": [], "members": [], "active": True}
        await ctx.db.execute(query, guildid, self.permdata[guildid])
        em = embedHR("green", "Hidden role created.")
        await ctx.send(embed=em)

    @hiddenrole.command(name="test")
    @checks.is_developer()
    async def testing(self, ctx):
        await self._getdata(ctx)



def setup(bot):
    bot.add_cog(Hiddenroles(bot))