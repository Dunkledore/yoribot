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
                if r["guild_id"] not in self.permdata or "__data_version__" not in self.permdata[r["guild_id"]] or\
                        self.permdata[r["guild_id"]]["__data_version__"] < self.DATA_VERSION:
                    await self._updatedata(ctx, r["guild_id"])
        await self._senddebug("```json\n"+str(self.permdata)+"```")

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
        await self._senddebug(f"Updated Data for guild {guildid}: ```json\n{guilddata}```")

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
                                    newperms = self._getuserperms(str(ctx.guild.id), userid)
                                else:
                                    newperms = self._getuserperms(str(ctx.guild.id), userid, rolename)
                                for chanid in newperms["deny"]:
                                    self.bot.get_channel(chanid).set_permissions(user, read_messages=False)
                                for chanid in newperms["allow"]:
                                    self.bot.get_channel(chanid).set_permissions(user, read_messages=True)

    @commands.group(invoke_without_command=True, aliases=["hr"])
    @commands.guild_only()
    @checks.is_mod()
    async def hiddenrole(self, ctx):
        """Command group for hidden role management."""
        prefix = self.bot.get_guild_prefixes(ctx.message.guild)[2]
        em = embedHR("yellow", "This command group is used for management of hidden roles.\n" + prefix)
        await ctx.send(embed=em)

    @hiddenrole.command(name="create", usage="<role name>")
    @commands.guild_only()
    @checks.is_admin()
    async def create_hiddenrole(self, ctx, name):
        """Creates a hidden role with the given name."""
        guildid = str(ctx.guild.id)
        if guildid in self.permdata and name in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "This hidden role already exists."))
            return
        if guildid not in self.permdata:
            await self._updatedata(ctx, guildid)
        self.permdata[guildid][name] = {"deny": [], "allow": [], "members": [], "active": False}
        await self._updatedata(ctx, guildid)
        await ctx.send(embed=embedHR("green", "Hidden role created."))

    @hiddenrole.command(name="delete", usage="<role name>")
    @commands.guild_only()
    @checks.is_admin()
    async def remove_hiddenrole(self, ctx, name):
        """Deletes a hidden role and all associated permissions. If you want to keep the data for later, use deactivate instead."""
        guildid = str(ctx.guild.id)
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "No hidden roles have been set up for this server."))
            return
        if name not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a hidden role with that name."))
            return
        await ctx.send(embed=embedHR("yellow",
                                     f"Are you sure you want to delete the hidden role **{name}**?\n"
                                     "If you want to keep the data but deactivate the permissions,"
                                     "use `[p]hiddenrole deactivate` instead.", "Answer: `yes` or `no`"))
        try:
            reply = await self.bot.wait_for("message", check=lambda m:m.author==ctx.author and ctx.channel==m.channel,timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(embed=embedHR("red", "Deletion aborted due to timeout."))
        else:
            if reply is not None and reply.content.lower().strip() == "yes":
                self.permdata[guildid][name]["active"] = False
                await self._applydata(ctx, guild=guildid,role=name)
                self.permdata[guildid].pop(name)
                await self._updatedata(ctx, guildid)
            else:
                await ctx.send(embed=embedHR("red", "Deletion aborted. The data is safe."))

    @hiddenrole.command(name="activate", usage="<role name>")
    @commands.guild_only()
    @checks.is_admin()
    async def activate_role(self, ctx, rolename):
        """Activates the permissions for the specified hidden role."""
        guildid = str(ctx.guild.id)
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "No hidden roles have been set up for this server."))
            return
        if rolename not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a hidden role with that name."))
            return
        if self.permdata[guildid][rolename]["active"]:
            await ctx.send(embed=embedHR("yellow", "That role is already active."))
            return
        self.permdata[guildid][rolename]["active"] = True
        await self._updatedata(ctx, guildid)
        await self._applydata(ctx, guild=guildid, role=rolename)
        await ctx.send(embed=embedHR("green", "That role has been activated."))

    @hiddenrole.command(name="deactivate", usage="<role name>")
    @commands.guild_only()
    @checks.is_admin()
    async def deactivate_role(self, ctx, rolename):
        """Deactivates the permissions for the specified hidden role."""
        guildid = str(ctx.guild.id)
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "No hidden roles have been set up for this server."))
            return
        if rolename not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a hidden role with that name."))
            return
        if not self.permdata[guildid][rolename]["active"]:
            await ctx.send(embed=embedHR("yellow", "That role is not active."))
            return
        self.permdata[guildid][rolename]["active"] = False
        await self._updatedata(ctx, guildid)
        await self._applydata(ctx, guild=guildid, role=rolename)
        await ctx.send(embed=embedHR("green", "That role has been deactivated."))

    @hiddenrole.group(invoke_without_command=False)
    @checks.is_mod()
    async def user(self, ctx):
        pass

    @user.command(name="add", usage="<role name> <user mention>")
    @commands.guild_only()
    @checks.is_mod()
    async def add_user_to_role(self, ctx, rolename, user: discord.User):
        """Adds a user to the specified role."""
        guildid = str(ctx.guild.id)
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "This server doesn't have any hidden roles set up."))
            return
        if rolename not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a role with this name."))
            return
        if user.id not in self.permdata[guildid][rolename]["members"]:
            self.permdata[guildid][rolename]["members"].append(user.id)
            await self._updatedata(ctx, guildid)
            await ctx.send(embed=embedHR("green", f"{user.mention} now has the role {rolename}."))
            if self.permdata[rolename]["active"]:
                await self._applydata(ctx, guild=str(ctx.guild.id), user=user.id, role=rolename)

    @user.command(name="remove", usage="<role name> <user mention>")
    @commands.guild_only()
    @checks.is_mod()
    async def remove_user_from_role(self, ctx, rolename, user: discord.User):
        """Removes a user from the specified role."""
        guildid = str(ctx.guild.id)
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "This server doesn't have any hidden roles set up."))
            return
        if rolename not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a role with this name."))
            return
        if user.id in self.permdata[guildid][rolename]["members"]:
            self.permdata[guildid][rolename]["members"].remove(user.id)
            await self._updatedata(ctx, guildid)
            await ctx.send(embed=embedHR("green", f"{user.mention} doesn't have the role {rolename} anymore."))
            if self.permdata[rolename]["active"]:
                await self._applydata(ctx, guild=str(ctx.guild.id), user=user.id, role=rolename)

    @hiddenrole.group(name="perm", invoke_without_command=False)
    @checks.is_admin()
    async def perm(self, ctx):
        pass

    @perm.command(name="allow", usage="<role name> <channel mention>")
    @commands.guild_only()
    @checks.is_admin()
    async def allow_role_in_channel(self, ctx, rolename, channel):
        """Allows that role to see that channel. Only affects the \"Read Messages\" permission."""
        guildid = str(ctx.guild.id)
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "This server doesn't have any hidden roles set up."))
            return
        if rolename not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a role with this name."))
            return
        chanid = channel.id
        rdata = self.permdata[guildid][rolename]
        if chanid in rdata["allow"]:
            await ctx.send(em=embedHR("yellow", "That role already has access to that channel."))
        if chanid in rdata["deny"]:
            rdata["deny"].remove(chanid)
        rdata["allow"].append(chanid)
        await self._updatedata(ctx, guildid)
        if rdata["active"]:
            await self._applydata(ctx, guild=guildid,role=rolename)
        await ctx.send(em=embedHR("green",f"Members with the role \"{rolename}\" can now access to {channel.mention}."))

    @perm.command(name="deny", usage="<role name> <channel mention>")
    @commands.guild_only()
    @checks.is_admin()
    async def deny_role_in_channel(self, ctx, rolename, channel):
        """Denies that role access to that channel. Only affects the \"Read Messages\" permission."""
        guildid = str(ctx.guild.id)
        if guildid not in self.permdata:
            await ctx.send(embed=embedHR("red", "This server doesn't have any hidden roles set up."))
            return
        if rolename not in self.permdata[guildid]:
            await ctx.send(embed=embedHR("red", "Couldn't find a role with this name."))
            return
        chanid = channel.id
        rdata = self.permdata[guildid][rolename]
        if chanid in rdata["deny"]:
            await ctx.send(em=embedHR("yellow", "That role already has no access to that channel."))
        if chanid in rdata["allow"]:
            rdata["allow"].remove(chanid)
        rdata["deny"].append(chanid)
        await self._updatedata(ctx, guildid)
        if rdata["active"]:
            await self._applydata(ctx, guild=guildid,role=rolename)
        await ctx.send(em=embedHR("green",f"Members of the role \"{rolename}\" now can't access {channel.mention}."))

    @hiddenrole.command(name="test")
    @checks.is_developer()
    async def testing(self, ctx):
        """Sends test data to the developers."""
        await self._getdata(ctx)


def setup(bot):
    bot.add_cog(Hiddenroles(bot))
