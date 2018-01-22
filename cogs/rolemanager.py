import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils.paginator import FieldPages
import os
from .utils import checks
import math

class RoleManager:
    """Manages self-assignable roles."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json("data/rolemanager/settings.json")

    # Gets the group a role belongs to
    async def _roleinfo(self, message, role: str):
        for g in self.settings[str(message.guild.id)]['sars'].keys():
            for r in self.settings[str(message.guild.id)]['sars'][g].keys():
                if r.lower() == role.lower():
                    return g, self.settings[str(message.guild.id)]['sars'][g][r], r
        return None

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def iam(self, ctx, *, role):
        """Self-assign a role."""
        if str(ctx.message.guild.id) not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
            return
        rolename = role.replace("\"", "")
        roleinfo = await self._roleinfo(ctx.message, rolename)
        if roleinfo is None:
            em = discord.Embed(color=ctx.message.author.color, description="You cannot add that role. Yet...")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
        else:
            role = discord.utils.get(ctx.message.guild.roles, id=int(roleinfo[1]))
            await ctx.message.author.add_roles(role)
            em = discord.Embed(color=ctx.message.author.color, description=("You have been successfully assigned the role of \"" + role.name + "\"!"))
            em.set_author(name="Success!", icon_url="http://bit.ly/2qi2m3a")
            await ctx.send(embed=em)

    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if str(message.guild.id) not in self.settings:
            return

        prefixes = tuple(self.bot.get_guild_prefixes(message.guild))

        for p in prefixes:
            if message.content.startswith(p):
                role = message.content[len(p):]
                rolename = role.replace("\"", "")
                roleinfo = await self._roleinfo(message, rolename)
                if roleinfo is None:
                    return
                role = discord.utils.get(message.guild.roles, id=int(roleinfo[1]))
                await message.author.add_roles(role)
                em = discord.Embed(color=message.author.color, description=("You have been successfully assigned the role of \"" + role.name + "\"!"))
                em.set_author(name="Success!", icon_url="http://bit.ly/2qi2m3a")
                await message.channel.send(embed=em)
                return

    @commands.command()
    @commands.guild_only()
    async def listroles(self, ctx):
        """Lists the self-assignable roles this server has."""
        if str(ctx.message.guild.id) not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
            return
        elif self.settings[str(ctx.message.guild.id)]['sars'] == {}:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
            return
        else:
            title = "**The following are available for you to self-assign**:\n\n"
            firstrole = ""
            entries = {}
            for g in sorted(self.settings[str(ctx.message.guild.id)]['sars'].keys()):
                text = "**" + g + "**:\n"
                roles_text = ""
                for r in sorted(self.settings[str(ctx.message.guild.id)]['sars'][g].keys()):
                    roles_text += r + "**,** "
                    if firstrole == "":
                        firstrole = r
                    roles_text = (roles_text[:-6] if roles_text[-2] == "*" else roles_text) + "\n\n"
                entries[text] = roles_text

            paginator = FieldPages(ctx, entries=list(entries.items()))
            paginator.embed.title = title
            paginator.embed.set_author(name="Self-Assignable Roles", icon_url="http://bit.ly/2rnwE4T")

            
            paginator.embed.set_author(name="Self-Assignable Roles", icon_url="http://bit.ly/2rnwE4T")
            if len(self.bot.get_guild_prefixes(ctx.message.guild))<3:
                text = "To add roles use [p]<rolename>, for example [p]"+ firstrole
            else:
                text = "To add roles use " + str(self.bot.get_guild_prefixes(ctx.message.guild)[2])+ "<rolename>, for example " + str(self.bot.get_guild_prefixes(ctx.message.guild)[2]) + firstrole
            paginator.embed.set_footer(text=text)
            await paginator.paginate()

    async def addrole(self, ctx, name, group: str, *, role: str):
        """Adds a role to the list of self-assignable roles, if the name contains spaces put it in quotes (").
        Example:
        [p]iam add "role name" name of the role"""
        if not ctx.message.guild.me.permissions_in(ctx.message.channel).manage_roles:
            em = discord.Embed(color=ctx.message.author.color,
                               description="I do not have the manage roles permission here,"
                                           "I cannot assign roles to people untill I do.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
            return
        else:
            if str(ctx.message.guild.id) not in self.settings:
                self.settings[str(ctx.message.guild.id)] = {'sars': {}}
            if await self._roleinfo(ctx.message, name) is not None:
                em = discord.Embed(color=ctx.message.author.color, description="That role: " + role + " is already self-assignable.")
                em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
                await ctx.send(embed=em)
                return
            grole = discord.utils.get(ctx.guild.role_hierarchy, name=role)
            if not grole:
                await ctx.send("Role: " + role + " not found")
                return
            if group not in self.settings[str(ctx.message.guild.id)]['sars']:
                self.settings[str(ctx.message.guild.id)]['sars'][group] = {}
            for drole in ctx.guild.role_hierarchy:
                if drole.name == role:
                    self.settings[str(ctx.message.guild.id)]['sars'][group][name] = str(drole.id)
                    break

            
            self.save_settings()
            em = discord.Embed(color=ctx.message.author.color, description="The role has been added to the list!")
            em.set_author(name=role, icon_url="http://bit.ly/2qi2m3a")
            await ctx.send(embed=em)


    @commands.command()
    @commands.guild_only()
    @checks.is_mod()
    async def addroles(self, ctx, group, *, role_names: str):
        """Adds multiple addable roles at once, separated by <separator>."""
        for rolename in role_names.split(','):
            await self.addrole(ctx, rolename, group, role=rolename.strip())

    @commands.command()
    @commands.guild_only()
    @checks.is_mod()
    async def removerole(self, ctx, role):
        """Takes a role off the list of self-assignable roles."""
        if str(ctx.message.guild.id) not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="There are no self-assignable roles for this server.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
            return
        roleinfo = await self._roleinfo(ctx.message, role)
        if roleinfo is None:
            em = discord.Embed(color=ctx.message.author.color, description="That is not a valid self-assignable role.")
            em.set_author(name=role, icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
            return
        else:
            del self.settings[str(ctx.message.guild.id)]['sars'][roleinfo[0]][roleinfo[2]]
            if len(self.settings[str(ctx.message.guild.id)]['sars'][roleinfo[0]]) == 0:
                del self.settings[str(ctx.message.guild.id)]['sars'][roleinfo[0]]
            self.save_settings()
            em = discord.Embed(color=ctx.message.author.color, description="The role has been removed")
            em.set_author(name=role, icon_url="http://bit.ly/2r2cpXh")
            await ctx.send(embed=em)

    @commands.command()
    @commands.guild_only()
    async def iamnot(self, ctx, role):
        """Removes a self-assignable role from you."""
        if str(ctx.message.guild.id) not in self.settings:
            em = discord.Embed(color=ctx.message.author.color,
                               description="This server has no self-assignable roles I can remove.")
            em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)
            return
        roleinfo = await self._roleinfo(ctx.message, role)
        if roleinfo is None:
            em = discord.Embed(color=ctx.message.author.color, description="That is not a valid self-assignable role.")
            em.set_author(name=role, icon_url="http://bit.ly/2qlsl5I")
            em.set_footer(
                text="If the role has spaces use quotations when trying to remove it. *role remove \"Example 1\"")
            await ctx.send(embed=em)
        else:
            try:
                if not ctx.message.guild.me.permissions_in(ctx.message.channel).manage_roles:
                    em = discord.Embed(color=ctx.message.author.color,
                                       description="I do not have the manage roles permission here,"
                                                   "I cannot remove roles from you untill I do.")
                    em.set_author(name="Uh-oh", icon_url="http://bit.ly/2qlsl5I")
                    await ctx.send(embed=em)
                    return
                else:
                    role = discord.utils.get(ctx.message.guild.roles, id=int(roleinfo[1]))
                    await ctx.message.author.remove_roles(role)
                    em = discord.Embed(color=ctx.message.author.color, description="Role removed")
                    em.set_author(name=role, icon_url="http://bit.ly/2r2cpXh")
                    await ctx.send(embed=em)
                    return
            except Exception as e:
                em = discord.Embed(color=ctx.message.author.color, description="An error occured removing the role")
                em.set_author(name=e.__class__.__name__, icon_url="http://bit.ly/2qlsl5I")
                await ctx.send(embed=em)

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
