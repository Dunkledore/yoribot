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
        self.DATA_VERSION = 2

    async def _senddebug(self, message):
        await self.bot.get_channel(381089525880979467).send(message)

    async def _getdata(self, ctx, server=None):
        if server is None:
            query = "SELECT * FROM hiddenroles"
            results = await ctx.db.fetch(query)
            for r in results:
                self.permdata[r["guild_id"]] = r["permission_data"]
                if self.permdata[r["guild_id"]]["__data__version__"] < self.DATA_VERSION:
                    await self._updatedata(ctx, r["guild_id"])
        await self._senddebug(str(self.permdata))

    async def _updatedata(self, ctx, guildid):
        if not guildid in self.permdata:
            self.permdata[guildid] = {"__data_version__": 1}
            init = True
        else:
            init = False
        guilddata = self.permdata[guildid]
        version = guilddata["__data_version__"] or 0
        if version < 2:
            guilddata["_18+"] = {"deny": [], "allow": [], "members": [], "active": False}
            guilddata["_<18"] = {"deny": [], "allow": [], "members": [], "active": False}
            guilddata["__data_version__"] = 2
        if not init:
            query = "UPDATE hiddenroles SET permission_data = $2 WHERE guild_id = $1"
        else:
            query = "INSERT INTO hiddenroles (guild_id, permission_data) VALUES ($1, $2)"
        await ctx.db.execute(query, guildid, guilddata)
        await self._senddebug(f"Updated Data for guild {guildid}: {guilddata}")

    async def _getuserperms(self, guildid, userid, excluderole=""):
        guilddata = self.permdata[guildid]
        retdata = {"deny": [], "allow": []}
        for role in guilddata:
            if not role == excluderole and guilddata[role]["active"] > 0:
                if userid in guilddata[role]["members"]:
                    for chanid in guilddata[role]["deny"]:
                        if chanid not in retdata["deny"] and chanid not in retdata["allow"]:
                            retdata["deny"].append(chanid)
                    for chanid in guilddata[role]["allow"]:
                        if chanid in retdata["deny"]:
                            retdata["deny"].remove(chanid)
                        if chanid not in retdata["allow"]:
                            retdata["allow"].append(chanid)
        return retdata

    async def _applydata(self, ctx, *, guild=-1, user=-1, role=""):
        for guild_id in self.permdata:
            if guild == -1 or guild_id == guild:
                guilddata = self.permdata[guild_id]
                for rolename in guilddata:
                    if guilddata[rolename]["active"] and (role == "" or role == rolename):
                        for userid in guilddata[rolename]["members"]:
                            if user == -1 or user == userid:
                                user = ctx.guild.get_user(userid)
                                if guilddata[rolename]["active"]:
                                    newperms = self._getuserperms(ctx.guild.id, userid)
                                else:
                                    newperms = self._getuserperms(ctx.guild.id, userid, rolename)
                                for chanid in newperms["deny"]:
                                    self.bot.get_channel(chanid).set_permissions(user, read_messages=False)
                                for chanid in newperms["allow"]:
                                    self.bot.get_channel(chanid).set_permissions(user, read_messages=True)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.is_mod()
    async def hiddenrole(self, ctx):
        prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]
        em = embedHR("yellow", "This command group is used for management of hidden roles.\n"+prefix)
        await ctx.send(embed=em)

    @hiddenrole.command(name="create", usage="<role name>")
    @commands.guild_only()
    @checks.is_admin()
    async def create_hiddenrole(self, ctx, name):
        guildid = ctx.guild.id
        if guildid in self.permdata and name in self.permdata[guildid]:
            em = embedHR("red", "This hidden role already exists.")
            await ctx.send(embed=em)
            return
        if guildid not in self.permdata:
            await self._updatedata(ctx, guildid)
        self.permdata[guildid][name] = {"deny": [], "allow": [], "members": [], "active": False}
        await self._updatedata(ctx, guildid)
        em = embedHR("green", "Hidden role created.")
        await ctx.send(embed=em)

    @hiddenrole.command(name="adduser", usage="<role name> <user mention>")
    @commands.guild_only()
    @checks.is_mod()
    async def add_user_to_role(self, ctx, rolename, user):
        guildid = ctx.guild.id
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "This server doesn't have any hidden roles setup."))
            return
        if rolename not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a role with this name."))
            return
        if user.id not in self.permdata[guildid][rolename]["members"]:
            self.permdata[guildid][rolename]["members"].append(user.id)
            await self._updatedata(ctx, guildid)
            await ctx.send(embed=embedHR("green", f"{user.mention} now has the role {rolename}."))
            if self.permdata[rolename]["active"]:
                self._applydata(ctx, guild=ctx.guild.id, user=user.id, role=rolename)

    @hiddenrole.command(name="test")
    @checks.is_developer()
    async def testing(self, ctx):
        await self._getdata(ctx)


def setup(bot):
    bot.add_cog(Hiddenroles(bot))