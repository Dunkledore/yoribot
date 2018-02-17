from discord.ext import commands
from .utils import checks, db, time, cache
from collections import Counter, defaultdict
from inspect import cleandoc

import re
import json
import discord
import enum
from datetime import datetime, timedelta
import asyncio
import argparse, shlex
import logging
import asyncpg
from .utils import checks
from random import choice
from cogs.utils.dataIO import dataIO
import os


log = logging.getLogger(__name__)

## Misc utilities

class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)

class RaidMode(enum.Enum):
    off = 0
    on = 1
    strict = 2

    def __str__(self):
        return self.name

## Tables

class GuildConfig(db.Table, table_name='guild_mod_config'):
    id = db.Column(db.Integer(big=True), primary_key=True)
    raid_mode = db.Column(db.Integer(small=True))
    broadcast_channel = db.Column(db.Integer(big=True))
    mention_count = db.Column(db.Integer(small=True))
    safe_mention_channel_ids = db.Column(db.Array(db.Integer(big=True)))

## Configuration

class ModConfig:
    __slots__ = ('raid_mode', 'id', 'bot', 'broadcast_channel_id', 'mention_count', 'safe_mention_channel_ids')

    @classmethod
    async def from_record(cls, record, bot):
        self = cls()

        # the basic configuration
        self.bot = bot
        self.raid_mode = record['raid_mode']
        self.id = record['id']
        self.broadcast_channel_id = record['broadcast_channel']
        self.mention_count = record['mention_count']
        self.safe_mention_channel_ids = set(record['safe_mention_channel_ids'] or [])
        return self

    @property
    def broadcast_channel(self):
        guild = self.bot.get_guild(self.id)
        return guild and guild.get_channel(self.broadcast_channel_id)

## Converters

class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
        else:
            can_execute = ctx.author.id == ctx.bot.owner_id or \
                          ctx.author == ctx.guild.owner or \
                          ctx.author.top_role > m.top_role

            if not can_execute:
                raise commands.BadArgument('You cannot do this action on this user due to role hierarchy.')
            return m.id

class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        ban_list = await ctx.guild.bans()
        try:
            member_id = int(argument, base=10)
            entity = discord.utils.find(lambda u: u.user.id == member_id, ban_list)
        except ValueError:
            entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument("Not a valid previously-banned member.")
        return entity

class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = f'{ctx.author} (ID: {ctx.author.id}): {argument}'

        if len(ret) > 512:
            reason_max = 512 - len(ret) - len(argument)
            raise commands.BadArgument(f'reason is too long ({len(argument)}/{reason_max})')
        return ret

## The actual cog

class Mod:
    """Moderation related commands."""

    def __init__(self, bot):
        self.bot = bot

        # guild_id: set(user_id)
        self._recently_kicked = defaultdict(set)
        self.media_count = {} #For anti media/image spam
        self.location = 'data/antilink/settings.json'
        self.json = dataIO.load_json(self.location)
        self.regex = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.gg|discordapp\.com\/invite)\b([-a-zA-Z0-9/]*)>?")
        self.regex_discordme = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.me\/)\b([-a-zA-Z0-9/]*)>?")
        self.kickmessages = ["Don't let the door hit you on your way out!","About time","Now we're cooking with gas!",
                            "You don't have to go home, but you can't stay here.", "Did I do that?"]
        self.banmessages = ["Don't let the door hit you on your way out!","About time","Now we're cooking with gas!",
                            "You don't have to go home, but you can't stay here.", "Did I do that?"]
        self.unbanmessages = ["Don't let the door hit you on your way out!","About time","Now we're cooking with gas!",
                            "You don't have to go home, but you can't stay here.", "Did I do that?"]

    def __repr__(self):
        return '<cogs.Mod>'

    async def __error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, discord.Forbidden):
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = "I do not have permission to execute this action."))
            elif isinstance(original, discord.NotFound):
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = f'This entity does not exist: {original.text}'))
            elif isinstance(original, discord.HTTPException):
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ='Somehow, an unexpected error occurred. Try again later?'))

    async def get_mod_channel(self, guild :discord.Guild):
        query = "SELECT * FROM mod_config WHERE guild_id = $1"
        results = await self.bot.pool.fetch(query, guild.id)
        if results:
            mod_channel_id = results[0]["mod_channel"]
            return guild.get_channel(mod_channel_id)
        return None

    @cache.cache()
    async def get_guild_config(self, guild_id):
        query = """SELECT * FROM guild_mod_config WHERE id=$1;"""
        async with self.bot.pool.acquire() as con:
            record = await con.fetchrow(query, guild_id)
            if record is not None:
                return await ModConfig.from_record(record, self.bot)
            return None

    async def on_reaction_add(self, reaction, user):
        if reaction.emoji != '\U0000274c':
            return
        con = self.bot.pool
        query = "SELECT * FROM mod_config WHERE guild_id = $1"
        number = await con.fetchrow(query, reaction.message.guild.id)

        if number is None:
            return

        if number[2] == 0:
            return

        for sreaction in reaction.message.reactions:
            if (sreaction.count >= number[2]) and (ord(sreaction.emoji) == 10060):
                await reaction.message.delete()

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def antilinkownerdm(self, ctx):
        """Enable or disable notifications to the server owner via DM when a link is shared in the server."""
        serverid = ctx.message.guild.id
        if str(serverid) not in self.json:        
            self.json[str(serverid)] = {'toggle': False, 'message': '', 'dm': False, 'ownerdm': False}
        if self.json[str(serverid)]['ownerdm'] is True:
            self.json[str(serverid)]['ownerdm'] = False
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Owner DM now disabled'))
        elif self.json[str(serverid)]['ownerdm'] is False:
            self.json[str(serverid)]['ownerdm'] = True
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Owner DM now enabled'))
        dataIO.save_json(self.location, self.json)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def toggleantilink(self, ctx):
        """Enable or disable anti-link entirely (if disabled, members can share links to other Discord servers)."""
        serverid = ctx.message.guild.id
        if str(serverid) not in self.json:        
            self.json[str(serverid)] = {'toggle': False, 'message': '', 'dm': False, 'ownerdm': False}
        if self.json[str(serverid)]['toggle'] is True:
            self.json[str(serverid)]['toggle'] = False
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Antilink is now disabled'))
        elif self.json[str(serverid)]['toggle'] is False:
            self.json[str(serverid)]['toggle'] = True
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Antilink is now enabled'))
        dataIO.save_json(self.location, self.json)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def antilinkmessage(self, ctx, *, text):
        """Customize the message sent to the person attempting to share a Discord link in your server."""
        serverid = ctx.message.guild.id
        if str(serverid) not in self.json:        
            self.json[str(serverid)] = {'toggle': False, 'message': '', 'dm': False, 'ownerdm': False}
        self.json[str(serverid)]['message'] = text
        dataIO.save_json(self.location, self.json)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Message is set'))
        if self.json[str(serverid)]['dm'] is False:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ Notice",
                                description ='Remember: Direct Messages on removal is disabled!\nEnable it with ``antilinktoggledm``'))

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def antilinktoggledm(self, ctx):
        """ Enable or Disable the anti-link DM"""
        serverid = ctx.message.guild.id
        if str(serverid) not in self.json:        
            self.json[str(serverid)] = {'toggle': False, 'message': '', 'dm': False, 'ownerdm': False}
        if self.json[str(serverid)]['dm'] is False:
            self.json[str(serverid)]['dm'] = True
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Enabled DMs on removal of invite links'))
        elif self.json[str(serverid)]['dm'] is True:
            self.json[str(serverid)]['dm'] = False
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Disabled DMs on removal of invite links'))
        dataIO.save_json(self.location, self.json)

    async def _new_message(self, message):
        """Finds the message and checks it for regex"""
        user = message.author
        if message.guild is None:
            return
        if str(message.guild.id) in self.json:
            if self.json[str(message.guild.id)]['toggle'] is True:
                if self.regex.search(message.content) is not None or self.regex_discordme.search(message.content) is not None:
                    roles = [r.name for r in user.roles]
                    #bot_admin = settings.get_server_admin(message.server) add these one day
                    #bot_mod = settings.get_server_mod(message.server)
                    if user.id == message.guild.owner.id:
                        return
                    #elif bot_admin in roles:
                    #    return
                    #elif bot_mod in roles:
                    #    return
                    #elif user.permissions_in(message.channel).manage_messages is True:
                    #    return
                    else:
                        asyncio.sleep(0.5)
                        await message.delete()
                        if (self.json[str(message.guild.id)]['dm'] is True) and (self.json[str(message.guild.id)]['message'] != ""):
                            if message.author.dm_channel is None:
                                await message.author.create_dm()
                            await message.author.dm_channel.send(self.json[str(message.guild.id)]['message'])
                        if self.json[str(message.guild.id)]['ownerdm'] is True:
                            if message.guild.owner.dm_channel is None:
                                await message.guild.owner.create_dm()
                            await message.guild.owner.dm_channel.send(message.author.mention + " posted " + message.content + " in " + message.channel.name)

    
    @commands.command()
    @checks.is_admin()
    async def reactiondelnumber(self, ctx, number=None):
        """Changes the number of \U0000274c reactions required to delete the message. Set to 0 to turn off."""
        if number is None:
            query = "SELECT * FROM mod_config WHERE guild_id = $1"
            conf = await ctx.db.fetchrow(query, ctx.message.guild.id)
            number = conf[2]
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ Notice",
                                description = 'The current number of reactions needed is ' + str(number)))
        else:
            insertquery = "INSERT INTO mod_config (guild_id, reaction_del_number) VALUES ($1, $2)"
            alterquery = "UPDATE mod_config SET reaction_del_number = $2 WHERE guild_id = $1"

            try:
                await ctx.db.execute(insertquery, ctx.guild.id, int(number))
            except asyncpg.UniqueViolationError:
                await ctx.db.execute(alterquery, ctx.guild.id, int(number))
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ='Updated the reaction delete threshold.'))

    @commands.command(no_pm=True)
    @checks.is_mod()
    async def kick(self, ctx, member: discord.Member, *, reason: ActionReason = None):
        """Kicks a member from the server.

        In order for this to work, the bot must have Kick Member permissions.

        To use this command you must have Kick Members permission.
        """

        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        await member.kick(reason=reason)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "👋  " + member.name + " was Kicked",
                                description = choice(self.kickmessages)))

    @commands.command(no_pm=True)
    @checks.is_mod()
    async def ban(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Bans a member from the server.

        You can also ban from ID to ban regardless whether they're
        in the server or not.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Ban Members permission.
        """
        person = discord.Member.name
        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        await ctx.guild.ban(discord.Object(id=member), reason=reason)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "🔨  " + person + " was Banned",
                                description = choice(self.banmessages)))

    @commands.command(no_pm=True)
    @checks.is_mod()
    async def massban(self, ctx, reason: ActionReason, *members: MemberID):
        """Mass bans multiple members from the server.

        You can also ban from ID to ban regardless whether they're
        in the server or not.

        Note that unlike the ban command, the reason comes first
        and is not optional.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Ban Members permission.
        """

        for member_id in members:
            await ctx.guild.ban(discord.Object(id=member_id), reason=reason)

        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "🔨  Ban Jackhammer ",
                                description = choice(self.banmessages)))

    @commands.command(no_pm=True)
    @checks.is_mod()
    async def softban(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Soft bans a member from the server.

        A softban is basically banning the member from the server but
        then unbanning the member as well. This allows you to essentially
        kick the member while removing their messages.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Kick Members permissions.
        """

        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        obj = discord.Object(id=member)
        await ctx.guild.ban(obj, reason=reason)
        await ctx.guild.unban(obj, reason=reason)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "👋  " + member.name + " was Kicked",
                                description = "Reason: " + reason + "\n" + choice(self.kickmessages)))
    @commands.command(no_pm=True)
    @checks.is_mod()
    async def unban(self, ctx, member: BannedMember, *, reason: ActionReason = None):
        """Unbans a member from the server.

        You can pass either the ID of the banned member or the Name#Discrim
        combination of the member. Typically the ID is easiest to use.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Ban Members permissions.
        """

        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        await ctx.guild.unban(member.user, reason=reason)
        if member.reason:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "🕊  " + member.name + " was Unbanned",
                                description = f'Unbanned {member.user} (ID: {member.user.id}), previously banned for {member.reason}.'))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "🕊  " + member.name + " was Unbanned",
                                description = choice(self.unbanmessages)))

    @commands.command(no_pm=True)
    @checks.is_mod()
    async def tempban(self, ctx, duration: time.FutureTime, member: MemberID, *, reason: ActionReason = None):
        """Temporarily bans a member for the specified duration.

        The duration can be a a short time form, e.g. 30d or a more human
        duration such as "until thursday at 3PM" or a more concrete time
        such as "2017-12-31".

        Note that times are in UTC.

        You can also ban from ID to ban regardless whether they're
        in the server or not.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Ban Members permission.
        """

        if reason is None:
            reason = f'Action done by {ctx.author} (ID: {ctx.author.id})'

        reminder = self.bot.get_cog('Reminder')
        if reminder is None:
            return await ctx.send('Sorry, this functionality is currently unavailable. Try again later?')

        await ctx.guild.ban(discord.Object(id=member), reason=reason)
        timer = await reminder.create_timer(duration.dt, 'tempban', ctx.guild.id, ctx.author.id, member, connection=ctx.db)
        await ctx.send(f'Banned ID {member} for {time.human_timedelta(duration.dt)}.')

    async def on_tempban_timer_complete(self, timer):
        guild_id, mod_id, member_id = timer.args

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            # RIP
            return

        moderator = guild.get_member(mod_id)
        if moderator is None:
            try:
                moderator = await self.bot.get_user_info(mod_id)
            except:
                # request failed somehow
                moderator = f'Mod ID {mod_id}'
            else:
                moderator = f'{moderator} (ID: {mod_id})'
        else:
            moderator = f'{moderator} (ID: {mod_id})'

        reason = f'Automatic unban from timer made on {timer.created_at} by {moderator}.'
        await guild.unban(discord.Object(id=member_id), reason=reason)

    @commands.command(name="mute", no_pm=True)
    @checks.is_mod()
    async def mute(self, ctx, user:discord.Member, channel:discord.TextChannel=None):
        """Mutes a user in the specified channel, if not specified, in the channel the command is used from."""
        if channel is None:
            channel = ctx.channel
        await channel.set_permissions(user,reason=f"Mute by {ctx.author}", send_messages=False)
        await ctx.send(f"{user.name} has been muted in {channel.name}.")

    @commands.command(name="unmute", no_pm=True)
    @checks.is_mod()
    async def unmute(self, ctx, user:discord.Member, channel:discord.TextChannel=None):
        """Unmutes a user in the specified channel, if not specified, in the channel the command is used from."""
        if channel is None:
            channel = ctx.channel
        await channel.set_permissions(user,reason=f"Unmute by {ctx.author}", send_messages=None)
        await ctx.send(f"{user.name} has been unmuted in {channel.name}.")

    @commands.command(name="muteall", no_pm=True)
    @checks.is_mod()
    async def muteall(self, ctx, user:discord.Member):
        """Mutes a user in all channels of this server."""
        for tchan in ctx.guild.text_channels:
            await tchan.set_permissions(user, reason=f"Mute in all channels by {ctx.author}", send_messages=False)
        await ctx.send(f"{user.name} has been muted in this server.")

    @commands.command(name="unmuteall", no_pm=True)
    @checks.is_mod()
    async def unmuteall(self, ctx, user:discord.Member):
        """Unmutes a user in all channels of this server."""
        for tchan in ctx.guild.text_channels:
            if tchan.overwrites_for(user) and not tchan.overwrites_for(user).is_empty():
                await tchan.set_permissions(user, reason=f"Unmute in all channels by {ctx.author}", send_messages=None)
        await ctx.send(f"{user.name} has been unmuted in this server.")

    @commands.command(name="cleanoverrides", no_pm=True)
    @checks.is_admin()
    async def pruneperms(self, ctx):
        """Removes empty user-specific permission overrides from the server (manual channel permissions) ."""
        count = 0
        for tchan in ctx.guild.text_channels:
            for overwrite in tchan.overwrites:
                if overwrite[1].is_empty():
                    # tchan.overwrites.remove(overwrite)
                    await tchan.set_permissions(overwrite[0], overwrite=None)
                    count += 1
        await ctx.send("No overwrites to clean up." if count == 0 else f"Cleaned up {count} overwrites.")

    @commands.group(invoke_without_command=True, no_pm=True)
    @checks.is_mod()
    async def mentionspam(self, ctx, count: int=None):
        """Enables auto-banning accounts that spam mentions.

        If a message contains `count` or more mentions then the
        bot will automatically attempt to auto-ban the member.
        The `count` must be greater than 3. If the `count` is 0
        then this is disabled.

        This only applies for user mentions. Everyone or Role
        mentions are not included.

        To use this command you must have the Ban Members permission.
        """

        if count is None:
            query = """SELECT mention_count, COALESCE(safe_mention_channel_ids, '{}') AS channel_ids
                       FROM guild_mod_config
                       WHERE id=$1;
                    """

            row = await ctx.db.fetchrow(query, ctx.guild.id)
            if row is None or not row['mention_count']:
                return await ctx.send('This server has not set up mention spam banning.')

            ignores = ', '.join(f'<#{e}>' for e in row['channel_ids']) or 'None'
            return await ctx.send(f'- Threshold: {row["mention_count"]} mentions\n- Ignored Channels: {ignores}')

        if count == 0:
            query = """UPDATE guild_mod_config SET mention_count = NULL WHERE id=$1;"""
            await ctx.db.execute(query, ctx.guild.id)
            self.get_guild_config.invalidate(self, ctx.guild.id)
            return await ctx.send('Auto-banning members has been disabled.')

        if count <= 3:
            await ctx.send('\N{NO ENTRY SIGN} Auto-ban threshold must be greater than three.')
            return

        query = """INSERT INTO guild_mod_config (id, mention_count, safe_mention_channel_ids)
                   VALUES ($1, $2, '{}')
                   ON CONFLICT (id) DO UPDATE SET
                       mention_count = $2;
                """
        await ctx.db.execute(query, ctx.guild.id, count)
        self.get_guild_config.invalidate(self, ctx.guild.id)
        await ctx.send(f'Now auto-banning members that mention more than {count} users.')

    @mentionspam.command(name='ignore', aliases=['bypass'])
    async def mentionspam_ignore(self, ctx, *channels: discord.TextChannel):
        """Specifies what channels ignore mentionspam auto-bans.

        If a channel is given then that channel will no longer be protected
        by auto-banning from mention spammers.

        To use this command you must have the Ban Members permission.
        """

        query = """UPDATE guild_mod_config
                   SET safe_mention_channel_ids =
                       ARRAY(SELECT DISTINCT * FROM unnest(COALESCE(safe_mention_channel_ids, '{}') || $2::bigint[]))
                   WHERE id = $1;
                """

        if len(channels) == 0:
            return await ctx.send('Missing channels to ignore.')

        channel_ids = [c.id for c in channels]
        await ctx.db.execute(query, ctx.guild.id, channel_ids)
        self.get_guild_config.invalidate(self, ctx.guild.id)
        await ctx.send(f'Mentions are now ignored on {", ".join(c.mention for c in channels)}.')

    @mentionspam.command(name='unignore', aliases=['protect'])
    async def mentionspam_unignore(self, ctx, *channels: discord.TextChannel):
        """Specifies what channels to take off the ignore list.

        To use this command you must have the Ban Members permission.
        """

        if len(channels) == 0:
            return await ctx.send('Missing channels to protect.')

        query = """UPDATE guild_mod_config
                   SET safe_mention_channel_ids =
                       ARRAY(SELECT element FROM unnest(safe_mention_channel_ids) AS element
                             WHERE NOT(element = ANY($2::bigint[])))
                   WHERE id = $1;
                """

        await ctx.db.execute(query, ctx.guild.id, [c.id for c in channels])
        self.get_guild_config.invalidate(self, ctx.guild.id)
        await ctx.send('Updated mentionspam ignore list.')

    @commands.group(aliases=['purge'], no_pm=True)
    @checks.is_mod()
    async def clear(self, ctx):
        """Removes messages that meet a criteria.

        In order to use this command, you must have Manage Messages permissions.
        Note that the bot needs Manage Messages as well. These commands cannot
        be used in a private message.

        When the command is done doing its work, you will get a message
        detailing which users got removed and how many messages got removed.
        """

        if ctx.invoked_subcommand is None:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='clear')

    async def do_removal(self, ctx, limit, predicate, *, before=None, after=None):
        if limit > 2000:
            return await ctx.send(f'Too many messages to search given ({limit}/2000)')

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        try:
            deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
        except discord.Forbidden as e:
            return await ctx.send('I do not have permissions to delete messages.')
        except discord.HTTPException as e:
            return await ctx.send(f'Error: {e} (try a smaller search?)')

        spammers = Counter(m.author.display_name for m in deleted)
        deleted = len(deleted)
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'**{name}**: {count}' for name, count in spammers)

        to_send = '\n'.join(messages)

        if len(to_send) > 2000:
            await ctx.send(f'Successfully removed {deleted} messages.', delete_after=10)
            await ctx.message.delete()
        else:
            await ctx.send(to_send, delete_after=10)
            await ctx.message.delete()

    @clear.command()
    async def embeds(self, ctx, search=100):
        """Removes messages that have embeds in them."""
        await self.do_removal(ctx, search, lambda e: len(e.embeds))

    @clear.command()
    async def files(self, ctx, search=100):
        """Removes messages that have attachments in them."""
        await self.do_removal(ctx, search, lambda e: len(e.attachments))

    @clear.command()
    async def images(self, ctx, search=100):
        """Removes messages that have embeds or attachments."""
        await self.do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @clear.command(name='all')
    async def _remove_all(self, ctx, search=100):
        """Removes all messages."""
        await self.do_removal(ctx, search, lambda e: True)

    @clear.command()
    async def user(self, ctx, member: discord.Member, search=100):
        """Removes all messages by the member."""
        await self.do_removal(ctx, search, lambda e: e.author == member)

    @clear.command()
    async def contains(self, ctx, *, substr: str):
        """Removes all messages containing a substring.

        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.send('The substring length must be at least 3 characters.')
        else:
            await self.do_removal(ctx, 100, lambda e: substr in e.content)

    @clear.command(name='bot')
    async def _bot(self, ctx, prefix=None, search=100):
        """Removes a bot user's messages and messages with their optional prefix."""

        def predicate(m):
            return m.author.bot or (prefix and m.content.startswith(prefix))

        await self.do_removal(ctx, search, predicate)

    @clear.command(name='emoji')
    async def _emoji(self, ctx, search=100):
        """Removes all messages containing custom emoji."""
        custom_emoji = re.compile(r'<:(\w+):(\d+)>')
        def predicate(m):
            return custom_emoji.search(m.content)

        await self.do_removal(ctx, search, predicate)

    @clear.command(name='reactions')
    async def _reactions(self, ctx, search=100):
        """Removes all reactions from messages that have them."""

        if search > 2000:
            return await ctx.send(f'Too many messages to search for ({search}/2000)')

        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()

        await ctx.send(f'Successfully removed {total_reactions} reactions.')

    @clear.command()
    async def custom(self, ctx, *, args: str):
        """A more advanced purge command.

        This command uses a powerful "command line" syntax.
        Most options support multiple values to indicate 'any' match.
        If the value has spaces it must be quoted.

        The messages are only deleted if all options are met unless
        the `--or` flag is passed, in which case only if any is met.

        The following options are valid.

        `--user`: A mention or name of the user to clear.
        `--contains`: A substring to search for in the message.
        `--starts`: A substring to search if the message starts with.
        `--ends`: A substring to search if the message ends with.
        `--search`: How many messages to search. Default 100. Max 2000.
        `--after`: Messages must come after this message ID.
        `--before`: Messages must come before this message ID.

        Flag options (no arguments):

        `--bot`: Check if it's a bot user.
        `--embeds`: Check if the message has embeds.
        `--files`: Check if the message has attachments.
        `--emoji`: Check if the message has custom emoji.
        `--reactions`: Check if the message has reactions
        `--or`: Use logical OR for all options.
        `--not`: Use logical NOT for all options.
        """
        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--user', nargs='+')
        parser.add_argument('--contains', nargs='+')
        parser.add_argument('--starts', nargs='+')
        parser.add_argument('--ends', nargs='+')
        parser.add_argument('--or', action='store_true', dest='_or')
        parser.add_argument('--not', action='store_true', dest='_not')
        parser.add_argument('--emoji', action='store_true')
        parser.add_argument('--bot', action='store_const', const=lambda m: m.author.bot)
        parser.add_argument('--embeds', action='store_const', const=lambda m: len(m.embeds))
        parser.add_argument('--files', action='store_const', const=lambda m: len(m.attachments))
        parser.add_argument('--reactions', action='store_const', const=lambda m: len(m.reactions))
        parser.add_argument('--search', type=int, default=100)
        parser.add_argument('--after', type=int)
        parser.add_argument('--before', type=int)

        try:
            args = parser.parse_args(shlex.split(args))
        except Exception as e:
            await ctx.send(str(e))
            return

        predicates = []
        if args.bot:
            predicates.append(args.bot)

        if args.embeds:
            predicates.append(args.embeds)

        if args.files:
            predicates.append(args.files)

        if args.reactions:
            predicates.append(args.reactions)

        if args.emoji:
            custom_emoji = re.compile(r'<:(\w+):(\d+)>')
            predicates.append(lambda m: custom_emoji.search(m.content))

        if args.user:
            users = []
            converter = commands.MemberConverter()
            for u in args.user:
                try:
                    user = await converter.convert(ctx, u)
                    users.append(user)
                except Exception as e:
                    await ctx.send(str(e))
                    return

            predicates.append(lambda m: m.author in users)

        if args.contains:
            predicates.append(lambda m: any(sub in m.content for sub in args.contains))

        if args.starts:
            predicates.append(lambda m: any(m.content.startswith(s) for s in args.starts))

        if args.ends:
            predicates.append(lambda m: any(m.content.endswith(s) for s in args.ends))

        op = all if not args._or else any
        def predicate(m):
            r = op(p(m) for p in predicates)
            if args._not:
                return not r
            return r

        args.search = max(0, min(2000, args.search)) # clamp from 0-2000
        await self.do_removal(ctx, args.search, predicate, before=args.before, after=args.after)
    
    @commands.command()
    @checks.is_mod()
    async def clearinvites(self, ctx, uses=1):
        all_invites = await ctx.guild.invites()

        invites = [i for i in all_invites if i.uses <= uses and i.created_at < (datetime.utcnow() - timedelta(hours=1))]

        if not invites:
            await ctx.send('I didn\'t find any invites matching your criteria')
            return

        message = await ctx.send('Ok, a total of {} invites created by {} users with {} total uses would be pruned.'.format(
                len(invites),
                len({i.inviter.id for i in invites}),
                sum(i.uses for i in invites)))   

        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(reaction, user):
            if user is None or user.id != ctx.author.id:
                return False

            if reaction.message.id != message.id:
                return False

            if reaction.emoji not in ['❌','✅']:
                return False
            return True

        reaction = None
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=120.0)
        except Exception as e:
            await ctx.send(str(e))
            await message.clear_reactions()
            return

        if reaction.emoji != '✅':
            await ctx.send("Invites not cleared")
            await message.clear_reactions()
            return

        for invite in invites:
            await invite.delete()
        await ctx.send("Invites cleared")
        await message.clear_reactions()

def check_folder():
    if not os.path.exists('data/antilink'):
        os.makedirs('data/antilink')

def check_file():
    f = 'data/antilink/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})

def setup(bot):
    check_folder()
    check_file()
    n=Mod(bot)
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')
