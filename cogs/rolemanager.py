import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
import os
from .utils import checks


class RoleManager:
    """Manages self-assignable roles."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json("data/rolemanager/settings.json")

    # Gets the group a role belongs to
    async def _roleinfo(self, ctx, role: str):
        for g in self.settings[ctx.message.server.id]['sars'].keys():
            for r in self.settings[ctx.message.server.id]['sars'][g].keys():
                if r.lower() == role.lower():
                    return g, self.settings[ctx.message.server.id]['sars'][g][r], r
        return None

    @commands.group(pass_context=True, invoke_without_command=True, no_pm=True)
    async def sar(self, ctx, *, role):
        """Self-assign a role."""
        if ctx.message.server.id not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return
        rolename = role.replace("\"", "")
        roleinfo = await self._roleinfo(ctx, rolename)
        if roleinfo is None:
            em = discord.Embed(color=ctx.message.author.color, description="You cannot add that role. Yet...")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
        else:
            role = discord.utils.get(ctx.message.server.roles, id=roleinfo[1])
            await self.bot.add_roles(ctx.message.author, role)
            em = discord.Embed(color=ctx.message.author.color, description="The role has been assigned to you!")
            em.set_author(name="Success!", icon_url="http://bit.ly/2qi2m3a")
            await self.bot.send_message(ctx.message.channel, embed=em)

    @sar.command(pass_context=True, no_pm=True)
    async def list(self, ctx):
        """Lists the self-assignable roles this server has."""
        if ctx.message.server.id not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return
        elif self.settings[ctx.message.server.id]['sars'] == {}:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return
        else:
            text = "**The following are available for you to self-assign**:\n\n"
            for g in sorted(self.settings[ctx.message.server.id]['sars'].keys()):
                text += "**" + g + "**:\n"
                for r in sorted(self.settings[ctx.message.server.id]['sars'][g].keys()):
                    text += r + "**,** "
                text = (text[:-6] if text[-2] == "*" else text) + "\n\n"
            em = discord.Embed(color=ctx.message.author.color, description=text)
            em.set_author(name="Self-Assignable Roles", icon_url="http://bit.ly/2rnwE4T")
            em.set_footer(text="To add roles use *sar rolename")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return

    @sar.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions()
    async def add(self, ctx, name, group: str, *, role: discord.Role):
        """Adds a role to the list of self-assignable roles, if the name contains spaces put it in quotes (").
        Example:
        [p]sar add "role name" name of the role"""
        if not ctx.message.server.me.permissions_in(ctx.message.channel).manage_roles:
            em = discord.Embed(color=ctx.message.author.color,
                               description="I do not have the manage roles permission here,"
                                           "I cannot assign roles to people untill I do.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return
        else:
            if ctx.message.server.id not in self.settings:
                self.settings[ctx.message.server.id] = {'sars': {}}
            if await self._roleinfo(ctx, name) is not None:
                em = discord.Embed(color=ctx.message.author.color, description="That role is already self-assignable.")
                em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
                await self.bot.send_message(ctx.message.channel, embed=em)
                return
            if group not in self.settings[ctx.message.server.id]['sars']:
                self.settings[ctx.message.server.id]['sars'][group] = {}
            self.settings[ctx.message.server.id]['sars'][group][name] = role.id
            self.save_settings()
            em = discord.Embed(color=ctx.message.author.color, description="The role has been added to the list!")
            em.set_author(name=role.name, icon_url="http://bit.ly/2qi2m3a")
            await self.bot.send_message(ctx.message.channel, embed=em)

    @sar.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions()
    async def unlist(self, ctx, role):
        """Takes a role off the list of self-assignable roles."""
        if ctx.message.server.id not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return
        roleinfo = await self._roleinfo(ctx, role)
        if roleinfo is None:
            em = discord.Embed(color=ctx.message.author.color, description="That is not a valid self-assignable role.")
            em.set_author(name=role, icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return
        else:
            del self.settings[ctx.message.server.id]['sars'][roleinfo[0]][roleinfo[2]]
            if len(self.settings[ctx.message.server.id]['sars'][roleinfo[0]]) == 0:
                del self.settings[ctx.message.server.id]['sars'][roleinfo[0]]
            self.save_settings()
            em = discord.Embed(color=ctx.message.author.color, description="The role has been removed")
            em.set_author(name=role, icon_url="http://bit.ly/2r2cpXh")
            await self.bot.send_message(ctx.message.channel, embed=em)

    @sar.command(pass_context=True, no_pm=True)
    async def remove(self, ctx, role):
        """Removes a self-assignable role from you."""
        if ctx.message.server.id not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="This server has no self-assignable roles I can remove.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await self.bot.send_message(ctx.message.channel, embed=em)
            return
        roleinfo = await self._roleinfo(ctx, role)
        if roleinfo is None:
            em = discord.Embed(color=ctx.message.author.color, description="That is not a valid self-assignable role.")
            em.set_author(name=role, icon_url="http://bit.ly/2qlsl5I")
            em.set_footer(
                text="If the role has spaces use quotations when trying to remove it. *role remove \"Example 1\"")
            await self.bot.send_message(ctx.message.channel, embed=em)
        else:
            try:
                if not ctx.message.server.me.permissions_in(ctx.message.channel).manage_roles:
                    em = discord.Embed(color=ctx.message.author.color,
                                       description="I do not have the manage roles permission here,"
                                                   "I cannot remove roles from you untill I do.")
                    em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
                    await self.bot.send_message(ctx.message.channel, embed=em)
                    return
                else:
                    role = discord.utils.get(ctx.message.server.roles, id=roleinfo[1])
                    await self.bot.remove_roles(ctx.message.author, role)
                    em = discord.Embed(color=ctx.message.author.color, description="Role removed")
                    em.set_author(name=role, icon_url="http://bit.ly/2r2cpXh")
                    await self.bot.send_message(ctx.message.channel, embed=em)
                    return
            except Exception as e:
                em = discord.Embed(color=ctx.message.author.color, description="An error occured removing the role")
                em.set_author(name=e.__class__.__name__, icon_url="http://bit.ly/2qlsl5I")
                await self.bot.send_message(ctx.message.channel, embed=em)

    def save_settings(self):
        dataIO.save_json("data/rolemanager/settings.json", self.settings)


def check_folders():
    if not os.path.exists("data/rolemanager"):
        print("Creating data/rolemanager folder...")
        os.makedirs("data/rolemanager")


def check_files():
    if not os.path.exists("data/rolemanager/settings.json"):
        print("Creating data/rolemanager/settings.json file...")
        dataIO.save_json("data/rolemanager/settings.json", {})


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(RoleManager(bot))
