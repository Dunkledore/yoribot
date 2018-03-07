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
    "on": False,
    "message_on": False
}


class MemberAudit:

    """Sets up a channel where you can receive notifications of when people join, leave, are banned or unbanned."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_path = "data/membership/settings.json"
        self.settings = dataIO.load_json(self.settings_path)
        self.deletedmessages = MaxList(500)
        self.invites = {}
        self.bot_bans = {} #used to find the user when the command ban was used

    async def cacheloop(self):
        while True:
            try:
                await self.bot.wait_until_ready()
                await self.cache_invites()
                await asyncio.sleep(3600)
            except Exception as e:
                print(e)

    async def cache_invites(self):
        for g in self.bot.guilds:
            if str(g.id) not in self.invites:
                self.invites[str(g.id)] = {}
            try:
                for i in await g.invites():
                    self.invites[str(g.id)][i.code] = (i.uses, i.inviter)
            except Exception as e:
                print("Can't get invited from {}: {}".format(g, e))

    def checksettings(self, guild):
        if str(guild.id) not in self.settings:
            self.settings[str(guild.id)] = deepcopy(default_settings)
            dataIO.save_json(self.settings_path, self.settings)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def membereventtoggle(self, ctx: commands.Context):
        """Turns member events on or off."""

        self.checksettings(ctx.guild)
        guild = ctx.message.guild
        guild_settings = self.settings[str(guild.id)]
        on = guild_settings["on"]

        if on:  # Turning off is easy no checks required
            on = False
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description="Membership events will now not be announced"))
        else:
            if "channel" not in guild_settings:  # No channel set ever
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="⚠ Error",
                                                   description="Can't turn member events on since no member audit channel has been set. Please set one first."))
                return
            # channel has been set but the bot cant find it. Most likely deleted
            elif not self.bot.get_channel(int(guild_settings["channel"])):
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="⚠ Error",
                                                   description="Can't turn member events on since the member audit channel has been deleted. Please set one first"))
                return
            else:
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="✅ Success",
                                                   description="Membership events will now be announced"))
                on = True

        self.settings[str(guild.id)]["on"] = on
        dataIO.save_json(self.settings_path, self.settings)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def messageeventtoggle(self, ctx: commands.Context):
        """Turns message events on or off."""

        self.checksettings(ctx.guild)
        guild = ctx.message.guild
        guild_settings = self.settings[str(guild.id)]
        on = guild_settings["message_on"]

        if on:  # Turning off is easy no checks required
            on = False
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description="Message events will now not be announced"))
        else:
            if "message_info_channel" not in guild_settings:  # No channel set ever
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="⚠ Error",
                                                   description="Can't turn message events on since no message audit channel has been set. Please set one first"))
                return
            # channel has been set but the bot cant find it. Most likely deleted
            elif not self.bot.get_channel(int(guild_settings["message_info_channel"])):
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="⚠ Error",
                                                   description="Can't turn message events on since the message audit channel has been deleted. Please set one first"))
                return
            else:
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                                   title="✅ Success",
                                                   description="Message events will now be announced"))
                on = True

        self.settings[str(guild.id)]["message_on"] = on
        dataIO.save_json(self.settings_path, self.settings)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def membereventchannel(self, ctx: commands.Context,
                           channel: discord.TextChannel):
        """Sets the text channel to which the member announcements will be sent."""

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
                                           description="I will now send member events to that channel"))
        channel = self.get_member_event_channel(guild)
        await channel.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description="Sending member events here"))

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def messageeventchannel(self, ctx: commands.Context,
                                 channel: discord.TextChannel):
        """Sets the text channel to which the meessage announcements will be sent."""

        self.checksettings(ctx.guild)
        guild = ctx.message.guild

        if not self.speak_permissions(guild, channel):
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="⚠ Error",
                                               description="I don't have permissions to talk in that channel."))
            return

        self.settings[str(guild.id)]["message_info_channel"] = str(channel.id)
        dataIO.save_json(self.settings_path, self.settings)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                           title="✅ Success",
                                           description="I will now send message events to that channel"))
        channel = self.get_message_event_channel(guild)
        await channel.send(embed=discord.Embed(color=ctx.message.author.color,
                                               title="✅ Success",
                                               description="Sending message events here"))

    async def member_join(self, member: discord.Member):
        
        self.checksettings(member.guild)
        guild = member.guild
        guild_settings = self.settings[str(guild.id)]

        used_invite = None
        for i in await guild.invites():
            if i.code not in self.invites[str(guild.id)]:
                self.invites[str(guild.id)][i.code] = (i.uses, i.inviter)
            uses, inviter = self.invites[str(guild.id)][i.code]
            if i.uses < uses:
                used_invite = i
                self.invites[str(guild.id)][i.code] = (i.uses, inviter)

        if not guild_settings["on"]:
            return

        member_event_channel = self.get_member_event_channel(guild)
        if not member_event_channel:
            return

        created = (datetime.datetime.utcnow() -
                   member.created_at).total_seconds() // 60
        if created < 30:  # or bannedin:
            colour = 0xdda453
        else:
            colour = 0x53dda4

        embed = discord.Embed(title="📥 Member Join",
                              description=member.mention, colour=colour)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Joined')
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name='ID', value=member.id)
        embed.add_field(name='Joined', value=member.joined_at)
        embed.add_field(name='Created', value=time.human_timedelta(
            member.created_at), inline=False)
        embed.add_field(name="Used Invite", value=used_invite.code + " created by " +
                        used_invite.inviter.display_name if used_invite.inviter is not None else " Server" + "({} uses)".format(used_invite.uses))

        if self.ban_permissions(guild):
            bannedin = ""
            for g in self.bot.guilds:
                try:
                    bans = await guild.bans()
                    for banentry in bans:
                        if member == banentry[1]:
                            bannedin += guild.name + '\n'
                except Exception as e:
                    print(e)
            if bannedin:
                embed.add_field(name='Banned In', value=bannedin)
        else:
            embed.add_field(name="No Ban Permissions",
                            value="This member may be banned in other Yori servers. Please enable the ban permissions for yori to see this in future")

        await member_event_channel.send(embed=embed)

    async def member_leave(self, member: discord.Member):
        self.checksettings(member.guild)
        guild = member.guild
        guild_settings = self.settings[str(guild.id)]

        if not guild_settings["on"]:
            return

        member_event_channel = self.get_member_event_channel(guild)
        if not member_event_channel:
            return

        embed = discord.Embed(
            title="📤 Member Leave",
            description=member.mention + member.name)
        embed.set_footer(text='Left')
        await member_event_channel.send(embed=embed)

    async def member_ban(self, guild, user: discord.User):
        self.checksettings(guild)
        guild_settings = self.settings[str(guild.id)]

        if not guild_settings["on"]:
            return


        member_event_channel = self.get_member_event_channel(guild)
        await member_event_channel.send("channel")

        if not member_event_channel:
            return

        try:

            embed = discord.Embed(title="🔨 Member Banned", description=user.name)
            embed.set_footer(text='Banned')
            if self.audit_log_permissions(guild):
                bans_info = await guild.audit_logs(action=discord.AuditLogAction.ban).flatten()
                ban_info = discord.utils.get(bans_info, target=user)
                banner = ban_info.user
                if banner = guild.me:
                    if user.id in bot_bans[guild.id]:
                        actual_banner = guild.get_member(bot_bans[guild.id][user.id])
                        if actual_banner:
                            banner = actual_banner
                embed.add_field(name="Banned by",
                                value=banner.name + " - " + banner.mention)
                reason = ban_info.reason
                if reason:
                    embed.add_field(name="Reason",
                                    value=reason)


            else:
                embed.add_field(
                    name="Banned by", value="Please enable access to AuditLogs to see this")

            await member_event_channel.send(embed=embed)
        except Exception as e:
            await member_event_channel.send(str(e))


    async def member_unban(self, guild, user: discord.User):
        self.checksettings(guild)
        guild_settings = self.settings[str(guild.id)]

        if not guild_settings["on"]:
            return

        member_event_channel = self.get_member_event_channel(guild)
        if not member_event_channel:
            return

        embed = discord.Embed(title="🔨 Member Unbanned", description=user.name)
        embed.set_footer(text='Unbanned')
        if self.audit_log_permissions(guild):
            unban_info = await guild.audit_logs(action=discord.AuditLogAction.unban, target=user).flatten()
            unbanner = unban_info[0].user
            embed.add_field(name="Unbanned by",
                            value=unbanner.name + " " + unbanner.mention)
        else:
            embed.add_field(
                name="Unbanned by", value="Please enable access to AuditLogs to see this")

        await member_event_channel.send(embed=embed)

    async def on_message_delete(self, message):
        self.checksettings(message.guild)
        guild = message.guild
        guild_settings = self.settings[str(guild.id)]

        if not guild_settings["message_on"]:
            return

        message_event_channel = self.get_message_event_channel(guild)
        if not message_event_channel:
            return

        embed = discord.Embed(title='📤 Message Deleted',
                              colour=discord.Colour.red())
        embed.set_author(name=message.author.name,
                         icon_url=message.author.avatar_url)
        embed.add_field(name='Message: ' + str(message.id),
                        value=message.content, inline=False)
        embed.add_field(name='Sent In:  ', value='Channel:  ' +
                        message.channel.name + '  Channel ID:  ' + str(message.channel.id))
        await message_event_channel.send(embed=embed)

    def get_member_event_channel(self, guild: discord.Guild):
        guild_settings = self.settings[str(guild.id)]
        if "channel" in guild_settings:
            return guild.get_channel(int(guild_settings["channel"]))
        else:
            return None

    def get_message_event_channel(self, guild: discord.Guild):
        guild_settings = self.settings[str(guild.id)]
        if "message_info_channel" in guild_settings:
            return guild.get_channel(int(guild_settings["message_info_channel"]))
        else:
            return None

    def speak_permissions(self, server: discord.Guild,
                          channel: discord.TextChannel=None):
        if not channel:
            channel = self.get_member_event_channel(server)
        member = server.get_member(self.bot.user.id)
        return member.permissions_in(channel).send_messages

    def ban_permissions(self, guild):
        member = guild.get_member(self.bot.user.id)
        return member.guild_permissions.ban_members

    def audit_log_permissions(self, guild):
        member = guild.get_member(self.bot.user.id)
        return member.guild_permissions.view_audit_log


def check_folders():
    if not os.path.exists("data/membership"):
        print("Creating data/membership directory...")
        os.makedirs("data/membership")


def check_files():
    f = "data/membership/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/membership/settings.json...")
        dataIO.save_json(f, {})


def setup(bot: commands.Bot):
    check_folders()
    check_files()
    n = MemberAudit(bot)
    bot.add_listener(n.member_join, "on_member_join")
    bot.add_listener(n.member_leave, "on_member_remove")
    bot.add_listener(n.member_ban, "on_member_ban")
    #bot.add_listener(n.hub_ban_audit, "on_member_ban")
    bot.add_listener(n.member_unban, "on_member_unban")
    bot.add_cog(n)
    bot.loop.create_task(n.cacheloop())
