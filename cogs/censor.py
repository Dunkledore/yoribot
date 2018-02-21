import discord
from discord.ext import commands
import os
import logging
from cogs.utils.dataIO import dataIO
from .utils import checks
import re

# Some magic values
ALL_CHANNELS = 'all'
MODE_INCLUSIVE = 'incl'  # deletes all messages matching
MODE_EXCLUSIVE = 'excl'  # delete all messages not matching
MODE_DISABLED = 'none'   # pattern disabled
MODES = [MODE_DISABLED, MODE_EXCLUSIVE, MODE_INCLUSIVE]

DATA_PATH = "data/recensor/"
JSON_PATH = DATA_PATH + "regexen.json"


__version__ = '1.5.0'


class ReCensor:

    # Data format:
    # {
    #  guildid (str): {
    #   channelid (str): {
    #     regex (str): mode (str from MODES)
    #     }
    #   }
    # }

    def __init__(self, bot):
        self.bot = bot
        self.regexen = dataIO.load_json(JSON_PATH)
        self.recache = {}
        self.analytics = CogAnalytics(self)
        bot.loop.create_task(self.compile_regexen())

    def _re_present(self, obj):
        """Determines if any patterns are set for a guild or channel"""
        if type(obj) is discord.guild:
            guild = obj
            if str(guild.id) in self.regexen:
                for relist in self.regexen[str(guild.id)].values():
                    if bool(relist):  # nonempty list
                        return True
                return False
            else:
                return False

        elif type(obj) is discord.TextChannel:
            guild = obj.guild
            channel = obj
            if str(channel.id) in self.regexen[str(guild.id)]:
                return bool(self.regexen[str(guild.id)][str(channel.id)])
            else:
                return False

        elif type(obj) is str:  # won't work with ALL_CHANNELS
            channel = self.bot.get_channel(obj)
            guild = channel.guild
            if str(channel.id) in self.regexen[str(guild.id)]:
                return bool(self.regexen[str(guild.id)][str(channel.id)])
            else:
                return False

    def _ls_excl(self, guild):
        """returns a list of channel IDs with exclusive filters"""
        clist = []
        if type(guild) is discord.guild:
            guild = str(guild.id)
        if guild in self.regexen:
            for c, relist in self.regexen[guild].items():
                if MODE_EXCLUSIVE in relist.values():
                    clist.append(c)
        return clist

    # Background cache regexen for speed
    async def compile_regexen(self):
        for s, channels in self.regexen.items():
            for regex in channels:
                self.recache[regex] = re.compile(regex)

    @commands.group(name='recensor', pass_context=True)
    @checks.is_mod()
    async def recensor(self, ctx):
        """Configure regular expression censorship"""
        if ctx.invoked_subcommand is None:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='recensor')

    @recensor.command(pass_context=True, name='list')
    async def _list(self, ctx, channel):
        """Lists regexes used to filter messages.
        Channel listing includes global patterns."""
        guild = ctx.message.guild
        self.regexen = dataIO.load_json(JSON_PATH)
        if not self._re_present(guild):
            await ctx.send('There are no filter patterns set for this guild.')
            return
        table = ' | '.join(['mode', 'pattern']) + '\n'  # header
        for c in self.regexen[str(guild.id)]:
            if c == ALL_CHANNELS and self._re_present(guild):
                    table += '\nguild-wide:\n'
            elif (channel and str(channel.id) == c) or not channel:
                if channel:
                    ch_obj = channel
                else:
                    ch_obj = self.bot.get_channel(c)
                if ch_obj is None:
                    table += '\n' + 'Channel ID %s (deleted):' % c + '\n'
                if self._re_present(ch_obj):
                    table += '\n#' + ch_obj.name + '\n'

            for regex, mode in self.regexen[str(guild.id)][c].items():
                table += ' | '.join([mode, regex]) + '\n'
        await ctx.send('```py\n' + table + '```')

    @recensor.command(pass_context=True, name='add')
    async def _add(self, ctx, pattern: str, mode, channel):
        """Adds a pattern to filter messages. Mods, bot admins, and the bot's
        owner are not subjected to the filter.
        If the pattern contains spaces, it must be put in double quotes. Single quotes will not work.

        mode is one of:
        incl: Default, filter messages that match the pattern
        excl: filter non-matching, only one allowed per channel or guild
        none: adds pattern to storage but doesn't apply filtering. Use recensor set to enable.

        To use channel, mode must also be specified. If channel is not specified,
        the filter is used across the entire guild."""
        guild = ctx.message.guild

        # initialize
        self.regexen = dataIO.load_json(JSON_PATH)
        if str(guild.id) not in self.regexen:
            self.regexen[str(guild.id)] = {}

        if pattern.startswith("'"):
            await ctx.send("Patterns cannot be specified within single quotes.")
            return

        if mode not in MODES:
            await ctx.send('"%s" is not a valid mode. You must specify one of `%s`.' % (mode, '`, `'.join(MODES)))
            return
        if mode == MODE_EXCLUSIVE:
            if ALL_CHANNELS in self._ls_excl(guild):
                await ctx.send("There is already a guild-wide exclusive filter. Remove or disable it first.")
                return
            if channel and str(channel.id) in self._ls_excl(guild):
                await ctx.send("That channel already has an exclusive filter. Remove or disable it first.")
                return
        cid = str(channel.id) if channel else ALL_CHANNELS
        if cid not in self.regexen[str(guild.id)]:
            self.regexen[str(guild.id)][cid] = {}
        self.regexen[str(guild.id)][cid][pattern] = mode
        await ctx.send('Pattern added.')
        dataIO.save_json(JSON_PATH, self.regexen)

    @recensor.command(pass_context=True, name='set')
    async def _set(self, ctx, mode, channel):
        """Lists regexes used to filter messages"""
        guild = ctx.message.guild
        self.regexen = dataIO.load_json(JSON_PATH)
        if not self._re_present(guild):
            await ctx.send('There are no patterns in the guild to modify.')
            return
        if mode not in MODES:
            self.bot.reply('"%s" is not a valid mode. You must specify one of `%s`.') % (mode, '`, `'.join(MODES))

        if mode == MODE_EXCLUSIVE:
            if ALL_CHANNELS in self._ls_excl(guild):
                await ctx.send("There is already a guild-wide exclusive filter. Remove or disable it first.")
                return
            if channel and str(channel.id) in self._ls_excl(guild):
                await ctx.send("That channel already has an exclusive filter. Remove or disable it first.")
                return

        re_list = {}
        i = 1
        table = ' | '.join(['#'.ljust(4), 'mode', 'pattern']) + '\n'  # header
        for c in self.regexen[str(guild.id)]:
            if c == ALL_CHANNELS and self._re_present(guild):
                    table += '\nguild-wide:\n'
            elif (channel and str(channel.id) == c) or not channel:
                if channel:
                    ch_obj = channel
                else:
                    ch_obj = self.bot.get_channel(c)
                if ch_obj is None:
                    table += '\n' + 'Channel ID %s (deleted):' % c + '\n'
                if self._re_present(ch_obj):
                    table += '\n#' + ch_obj.name + '\n'

            for regex, oldmode in self.regexen[str(guild.id)][c].items():
                table += ' | '.join([str(i).ljust(4), oldmode, regex]) + '\n'
                re_list[str(i)] = (str(guild.id), c, regex, oldmode)
                i += 1
        prompt = 'Choose the number of the pattern to set to `%s`:\n' % mode
        await ctx.send(prompt + '```py\n' + table + '```')

        msg = await self.bot.wait_for_message(author=ctx.message.author, timeout=15)
        if msg is None:
            return
        msg = msg.content.strip()
        if msg in re_list:
            sid, cid, regex, _ = re_list[msg]
            self.regexen[sid][cid][regex] = mode
            await ctx.send('Mode set.')
            dataIO.save_json(JSON_PATH, self.regexen)

    @recensor.command(pass_context=True, name='del')
    async def _del(self, ctx, channel):
        """Lists regexes used to filter messages"""
        guild = ctx.message.guild
        self.regexen = dataIO.load_json(JSON_PATH)
        if not self._re_present(guild):
            await ctx.send('There are no filter patterns set for this guild.')
            return
        re_list = {}
        i = 1
        table = ' | '.join(['#'.ljust(4), 'mode', 'pattern']) + '\n'  # header
        for c in self.regexen[str(guild.id)]:
            if c == ALL_CHANNELS and self._re_present(guild):
                    table += '\nguild-wide:\n'
            elif (channel and str(channel.id) == c) or not channel:
                if channel:
                    ch_obj = channel
                else:
                    ch_obj = self.bot.get_channel(c)
                if ch_obj is None:
                    table += '\n' + 'Channel ID %s (deleted):' % c + '\n'
                if self._re_present(ch_obj):
                    table += '\n#' + ch_obj.name + '\n'

            for regex, mode in self.regexen[str(guild.id)][c].items():
                table += ' | '.join([str(i).ljust(4), mode, regex]) + '\n'
                re_list[str(i)] = (str(guild.id), c, regex)
                i += 1
        prompt = 'Choose the number of the pattern to delete:\n'
        await ctx.send(prompt + '```py\n' + table + '```')
        msg = await self.bot.wait_for_message(author=ctx.message.author, timeout=15)
        if msg is None:
            return
        msg = msg.content.strip()
        if msg in re_list:
            sid, cid, regex = re_list[msg]
            del(self.regexen[sid][cid][regex])
            await ctx.send('Pattern removed.')
        dataIO.save_json(JSON_PATH, self.regexen)

    def immune_from_filter(self, message):
        """Tests message to see if it is exempt from filter. Taken from mod.py"""
        user = message.author
        guild = message.guild
        admin_role = self.bot.settings.get_guild_admin(guild)
        mod_role = self.bot.settings.get_guild_mod(guild)

        if str(user.id) == self.bot.settings.owner:
            return True
        elif discord.utils.get(user.roles, name=admin_role):
            return True
        elif discord.utils.get(user.roles, name=mod_role):
            return True
        else:
            return False

    async def on_message(self, message):
        # Fast checks
        if message.channel.is_private or self.bot.user == message.author \
         or not isinstance(message.author, discord.Member):
            return

        guild = message.guild
        sid = str(guild.id)
        can_delete = message.channel.permissions_for(guild.me).manage_messages

        # Owner, admins and mods are immune to the filter
        if self.immune_from_filter(message) or not can_delete:
            return

        if sid in self.regexen:
            patterns = {}
            # compile list of patterns from global and channel
            for key in [ALL_CHANNELS, str(message.channel.id)]:
                if key in self.regexen[sid]:
                    patterns.update(self.regexen[sid][key])
            # Iterate through patterns
            for regex, mode in patterns.items():
                # Skip disabled patterns
                if mode == MODE_DISABLED:
                    continue
                regex = self.recache[regex] if regex in self.recache else re.compile(regex)
                if (mode == MODE_EXCLUSIVE) != bool(regex.match(message.content)):  # xor
                    await self.bot.delete_message(message)

    async def on_message_edit(self, old_message, new_message):
        await self.on_message(new_message)

    async def on_command(self, command, ctx):
        if ctx.cog is self:
            self.analytics.command(ctx)

def check_folder():
    if not os.path.exists(DATA_PATH):
        log.debug('Creating folder: %s' % DATA_PATH)
        os.makedirs(DATA_PATH)


def check_file():
    if dataIO.is_valid_json(JSON_PATH) is False:
        log.debug('Creating json: %s' % JSON_PATH)
        dataIO.save_json(JSON_PATH, {})


def setup(bot):
    check_folder()
    check_file()
    n = ReCensor(bot)
    bot.add_cog(n)