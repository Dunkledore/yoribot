from copy import deepcopy
import os
import asyncio
import discord
import datetime
from discord.ext import commands
from .utils.maxlist import MaxList
from .utils.dataIO import dataIO
from .utils import checks, time, chat_formatting as cf

default_settings = {
    "on": False
}


class InviteAudit(object):
    """Sets up a channel where you can receive notifications of invites created, used, expired or deleted."""

    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.settings_path = "data/invites/settings.json"
        self.settings = dataIO.load_json(self.settings_path)
        self.invites = {}
        self.cachefirst_run = True
        self.unloaded = False

    async def cacheloop(self):
        while not self.unloaded:
            try:
                await self.bot.wait_until_ready()
                await self.cache_invites()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                self.unloaded = True
            except Exception:
                pass

    async def cache_invites(self):
        for g in self.bot.guilds:
            if str(g.id) in self.settings:
                guild_settings = self.settings[str(g.id)]
                if not guild_settings["on"]:
                    continue
                if str(g.id) not in self.invites:
                    self.invites[str(g.id)] = {}
                try:
                    guild_invites = await g.invites()
                    channel = self.get_invite_event_channel(g)
                    expiredinvs = []
                    for j in self.invites[str(g.id)]:
                        found = False
                        for l in guild_invites:
                            if l.code != self.invites[str(g.id)][j].code:
                                continue
                            found = True
                        if not found:
                            em = discord.Embed(title="📤 Invite expired or deleted", description="{} created by {} has expired or was deleted.".format(
                                self.invites[str(g.id)][j].code, self.invites[str(g.id)][j].inviter.name if self.invites[str(g.id)][j].inviter else "Server Widget"))
                            await channel.send(embed=em)
                            expiredinvs.append(self.invites[str(g.id)][j])
                    for x in expiredinvs:
                        del self.invites[str(g.id)][x.code]
                    for i in guild_invites:
                        if i.code in self.invites[str(g.id)]:
                            inv = self.invites[str(g.id)][i.code]
                            if inv.uses < i.uses:
                                uses = i.uses - inv.uses
                                em = discord.Embed(title="ℹ️ Invite Used", description="{} created by {} was recently used {} time(s) by user(s) to join this guild.".format(
                                    i.code, i.inviter.name if i.inviter else "Server Widget", uses))
                                await channel.send(embed=em)
                        elif not self.cachefirst_run:
                            em = discord.Embed(title="📥 New Invite", description="{} created by {}".format(
                                i.code, i.inviter.name if i.inviter else "Server Widget"))
                            await channel.send(embed=em)
                        self.invites[str(g.id)][i.code] = i
                except Exception as e:
                    print("Can't get invites from {}: {}".format(g, e))
        self.cachefirst_run = False

    def checksettings(self, guild):
        if str(guild.id) not in self.settings:
            self.settings[str(guild.id)] = deepcopy(default_settings)
            dataIO.save_json(self.settings_path, self.settings)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def inviteeventtoggle(self, ctx: commands.Context):
        """Toggles Invite events on or off."""

        self.checksettings(ctx.guild)
        guild = ctx.message.guild
        guild_settings = self.settings[str(guild.id)]
        on = guild_settings["on"]

        if on:
            on = False
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description="Invite events will now not be announced"))
        else:
            if "channel" not in guild_settings:
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="⚠ Error",
                                                   description="Can't turn invite events on since no invite audit channel has been set. Please set one first."))
                return
            # channel has been set but the bot cant find it. Most likely deleted
            elif not self.bot.get_channel(int(guild_settings["channel"])):
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="⚠ Error",
                                                   description="Can't turn invite events on since the invite audit channel has been deleted. Please set one first"))
                return
            else:
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="✅ Success",
                                                   description="Invite events will now be announced"))
                on = True

        self.settings[str(guild.id)]["on"] = on
        dataIO.save_json(self.settings_path, self.settings)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def inviteeventchannel(self, ctx: commands.Context,
                                 channel: discord.TextChannel):
        """Sets the text channel to which the invite announcements will be sent."""

        self.checksettings(ctx.guild)
        guild = ctx.message.guild

        if not self.speak_permissions(guild, channel):
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="⚠ Error",
                                               description="I don't have permissions to talk in that channel."))
            return

        self.settings[str(guild.id)]["channel"] = str(channel.id)
        dataIO.save_json(self.settings_path, self.settings)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                           title="✅ Success",
                                           description="I will now send invite events to that channel"))
        channel = self.get_invite_event_channel(guild)
        await channel.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description="Sending invite events here"))

    def get_invite_event_channel(self, guild: discord.Guild):
        guild_settings = self.settings[str(guild.id)]
        if "channel" in guild_settings:
            return guild.get_channel(int(guild_settings["channel"]))
        else:
            return None

    def speak_permissions(self, server: discord.Guild,
                          channel: discord.TextChannel=None):
        if not channel:
            channel = self.get_invite_event_channel(server)
        member = server.get_member(self.bot.user.id)
        return member.permissions_in(channel).send_messages


def check_folders():
    if not os.path.exists("data/invites"):
        print("Creating data/invites directory...")
        os.makedirs("data/invites")


def check_files():
    f = "data/invites/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/invites/settings.json...")
        dataIO.save_json(f, {})

task = None

def setup(bot: commands.Bot):
    check_folders()
    check_files()
    n = InviteAudit(bot)
    bot.add_cog(n)
    global task 
    task = bot.loop.create_task(n.cacheloop())

def teardown(bot: commands.Bot):
    task.cancel()