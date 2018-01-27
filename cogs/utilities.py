from discord.ext import commands
from .utils import checks, formats
from .utils.paginator import HelpPaginator, CannotPaginate
import discord
from collections import OrderedDict, deque, Counter
import os, datetime
import asyncio
import copy
import unicodedata
import inspect
import heapq
import os
from io import BytesIO
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
plt.switch_backend('agg')
from discord.ext import commands

class Prefix(commands.Converter):
    async def convert(self, ctx, argument):
        user_id = ctx.bot.user.id
        if argument.startswith((f'<@{user_id}>', f'<@!{user_id}>')):
            raise commands.BadArgument('That is a reserved prefix already in use.')
        return argument

class Utilities:
    """Commands for utilities related to Discord or the Bot itself."""

    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    async def __error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.command(name='help', hidden=True)
    async def _help(self, ctx, *, command: str = None):
        """Shows help about a command or the bot"""

        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command) or self.bot.get_command(command)

                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            await ctx.send(e)

    @commands.command(hidden=True)
    async def charinfo(self, ctx, *, characters: str, hidden=True):
        """Shows you information about a number of characters."""

        if len(characters) > 25:
            return await ctx.send(f'Too many characters ({len(characters)}/25)')

        def to_string(c):
            digit = f'{ord(c):x}'
            name = unicodedata.name(c, 'Name not found.')
            return f'`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>'

        await ctx.send('\n'.join(map(to_string, characters)))

    @commands.group(name='prefix', invoke_without_command=True)
    @checks.is_admin()
    async def prefix(self, ctx):
        """Manages the server's custom prefixes. To see the prefixes set for this server use this without any subcommands. """

        prefixes = self.bot.get_guild_prefixes(ctx.guild)

        # we want to remove prefix #2, because it's the 2nd form of the mention
        # and to the end user, this would end up making them confused why the
        # mention is there twice
        del prefixes[1]

        e = discord.Embed(title='Prefixes', colour=discord.Colour.blurple())
        e.set_footer(text=f'{len(prefixes)} prefixes')
        e.description = '\n'.join(f'{index}. {elem}' for index, elem in enumerate(prefixes, 1))
        await ctx.send(embed=e)

    @prefix.command(name='add', ignore_extra=False)
    @checks.is_mod()
    async def prefix_add(self, ctx, prefix: Prefix):
        """Allows you to set a custom prefix for your server."""

        current_prefixes = self.bot.get_raw_guild_prefixes(ctx.guild.id)
        current_prefixes.append(prefix)
        try:
            await self.bot.set_guild_prefixes(ctx.guild, current_prefixes)
        except Exception as e:
            await ctx.send(f'{ctx.tick(False)} {e}')
        else:
            await ctx.send(f'\N{OK HAND SIGN}')

    @prefix_add.error
    async def prefix_add_error(self, ctx, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.send("You've given too many prefixes. Either quote it or only do it one by one.")

    @prefix.command(name='remove', aliases=['delete'], ignore_extra=False)
    @checks.is_mod()
    async def prefix_remove(self, ctx, prefix: Prefix):
        """Removes a prefix from the list of custom prefixes."""

        current_prefixes = self.bot.get_raw_guild_prefixes(ctx.guild.id)

        try:
            current_prefixes.remove(prefix)
        except ValueError:
            return await ctx.send('I do not have this prefix registered.')

        try:
            await self.bot.set_guild_prefixes(ctx.guild, current_prefixes)
        except Exception as e:
            await ctx.send(f'{ctx.tick(False)} {e}')
        else:
            await ctx.send(f'\N{OK HAND SIGN}')

    @prefix.command(name='clear')
    @checks.is_mod()
    async def prefix_clear(self, ctx):
        """Removes all custom prefixes."""

        await self.bot.set_guild_prefixes(ctx.guild, [])
        await ctx.send(f'\N{OK HAND SIGN}')

    @commands.command(name='quit', hidden=True)
    @checks.is_developer()
    async def _quit(self, ctx):
        """Quits the bot."""
        await self.bot.logout()

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def info(self, ctx, *, member: discord.Member = None):
        """Shows info about a member."""

        if member is None:
            member = ctx.author

        e = discord.Embed()
        roles = [role.name.replace('@', '@\u200b') for role in member.roles]
        shared = sum(1 for m in self.bot.get_all_members() if m.id == member.id)
        voice = member.voice
        if voice is not None:
            vc = voice.channel
            other_people = len(vc.members) - 1
            voice = f'{vc.name} with {other_people} others' if other_people else f'{vc.name} by themselves'
        else:
            voice = 'Not connected.'

        e.set_author(name=str(member))
        e.set_footer(text='Member since').timestamp = member.joined_at
        e.add_field(name='ID', value=member.id)
        e.add_field(name='Servers', value=f'{shared} shared')
        e.add_field(name='Created', value=member.created_at)
        e.add_field(name='Voice', value=voice)
        e.add_field(name='Roles', value=', '.join(roles) if len(roles) < 10 else f'{len(roles)} roles')
        e.colour = member.colour

        if member.avatar:
            e.set_thumbnail(url=member.avatar_url)

        await ctx.send(embed=e)

    @info.command(name='server', aliases=['guild'], hidden=True)
    @commands.guild_only()
    async def server_info(self, ctx):
        """Shows info about the current server."""

        guild = ctx.guild
        roles = [role.name.replace('@', '@\u200b') for role in guild.roles]

        # we're going to duck type our way here
        class Secret:
            pass

        secret_member = Secret()
        secret_member.id = 0
        secret_member.roles = [guild.default_role]

        # figure out what channels are 'secret'
        secret_channels = 0
        secret_voice = 0
        text_channels = 0
        for channel in guild.channels:
            perms = channel.permissions_for(secret_member)
            is_text = isinstance(channel, discord.TextChannel)
            text_channels += is_text
            if is_text and not perms.read_messages:
                secret_channels += 1
            elif not is_text and (not perms.connect or not perms.speak):
                secret_voice += 1

        regular_channels = len(guild.channels) - secret_channels
        voice_channels = len(guild.channels) - text_channels
        member_by_status = Counter(str(m.status) for m in guild.members)

        e = discord.Embed()
        e.title = 'Info for ' + guild.name
        e.add_field(name='ID', value=guild.id)
        e.add_field(name='Owner', value=guild.owner)
        if guild.icon:
            e.set_thumbnail(url=guild.icon_url)

        if guild.splash:
            e.set_image(url=guild.splash_url)

        info = []

        info.append(ctx.tick(guild.member_count > 100, 'Large'))

        e.add_field(name='Info', value='\n'.join(map(str, info)))

        fmt = f'Text {text_channels} ({secret_channels} secret)\nVoice {voice_channels} ({secret_voice} locked)'
        e.add_field(name='Channels', value=fmt)

        fmt = f':green_apple: {member_by_status["online"]} ' \
              f':tangerine: {member_by_status["idle"]} ' \
              f':apple: {member_by_status["dnd"]} ' \
              f':black_circle:{member_by_status["offline"]}\n' \
              f'Total: {guild.member_count}'

        e.add_field(name='Members', value=fmt)
        e.add_field(name='Roles', value=', '.join(roles) if len(roles) < 10 else f'{len(roles)} roles')
        e.set_footer(text='Created').timestamp = guild.created_at
        await ctx.send(embed=e)

    async def say_permissions(self, ctx, member, channel):
        permissions = channel.permissions_for(member)
        e = discord.Embed(colour=member.colour)
        allowed, denied = [], []
        for name, value in permissions:
            name = name.replace('_', ' ').replace('guild', 'server').title()
            if value:
                allowed.append(name)
            else:
                denied.append(name)

        e.add_field(name='Allowed', value='\n'.join(allowed))
        e.add_field(name='Denied', value='\n'.join(denied))
        await ctx.send(embed=e)

    @commands.command()
    @commands.guild_only()
    async def permissions(self, ctx, member: discord.Member = None, channel: discord.TextChannel = None):
        """Shows a member's permissions in a specific channel."""
        channel = channel or ctx.channel
        if member is None:
            member = ctx.author

        await self.say_permissions(ctx, member, channel)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def botpermissions(self, ctx, *, channel: discord.TextChannel = None):
        """Shows the bot's permissions in a specific channel."""
        channel = channel or ctx.channel
        member = ctx.guild.me
        await self.say_permissions(ctx, member, channel)

    @commands.command(aliases=['invite'])
    async def join(self, ctx):
        """Provides the bot invite link."""
        perms = discord.Permissions.none()
        perms.read_messages = True
        perms.external_emojis = True
        perms.send_messages = True
        perms.manage_roles = True
        perms.manage_channels = True
        perms.ban_members = True
        perms.kick_members = True
        perms.manage_messages = True
        perms.embed_links = True
        perms.read_message_history = True
        perms.attach_files = True
        perms.add_reactions = True
        await ctx.send(f'<{discord.utils.oauth_url(self.bot.client_id, perms)}>')

    @commands.command(rest_is_raw=True, hidden=True)
    @checks.is_mod()
    async def echo(self, ctx, *, content):
        await ctx.send(content)

    def create_chart(self, top, others):
        plt.clf()
        sizes = [x[1] for x in top]
        labels = ["{} {:g}%".format(x[0], x[1]) for x in top]
        if len(top) >= 10:
            sizes = sizes + [others]
            labels = labels + ["Others {:g}%".format(others)]

        title = plt.title('User activity in the last 5000 messages')
        title.set_va("top")
        title.set_ha("left")
        plt.gca().axis("equal")
        colors = ['r', 'darkorange', 'gold', 'y', 'olivedrab', 'green', 'darkcyan', 'mediumblue', 'darkblue', 'blueviolet', 'indigo']
        pie = plt.pie(sizes, colors=colors, startangle=0)
        plt.legend(pie[0], labels, bbox_to_anchor=(0.7, 0.5), loc="center", fontsize=10,
                   bbox_transform=plt.gcf().transFigure)
        plt.subplots_adjust(left=0.0, bottom=0.1, right=0.45)
        image_object = BytesIO()
        plt.savefig(image_object, format='PNG')
        image_object.seek(0)
        return image_object

    @commands.command(pass_context=True)
    async def chanchart(self, ctx, channel : discord.TextChannel = None):
        """Generates a pie chart showing who the most active users were in the last 5000 messages of the given channel."""
        if not channel:
            channel = ctx.message.channel
        e = discord.Embed(description="Please wait one moment while I gather all the data...", colour=0x00ccff)
        em = await ctx.send(embed=e)

        history = []
        async for msg in channel.history(limit=5000):
            history.append(msg)
        msg_data = {'total count': 0, 'users': {}}

        for msg in history:
            if msg.author.bot:
                pass
            elif msg.author.name in msg_data['users']:
                msg_data['users'][msg.author.name]['msgcount'] += 1
                msg_data['total count'] += 1
            else:
                msg_data['users'][msg.author.name] = {}
                msg_data['users'][msg.author.name]['msgcount'] = 1
                msg_data['total count'] += 1

        for usr in msg_data['users']:
            pd = float(msg_data['users'][usr]['msgcount']) / float(msg_data['total count'])
            msg_data['users'][usr]['percent'] = round(pd * 100, 1)

        top_ten = heapq.nlargest(10, [(x, msg_data['users'][x][y])
                                      for x in msg_data['users']
                                      for y in msg_data['users'][x]
                                      if y == 'percent'], key=lambda x: x[1])
        others = 100 - sum(x[1] for x in top_ten)
        img = self.create_chart(top_ten, others)
        await ctx.send(file=discord.File(img, filename='chatchart.jpg'))

def check_folders():
    if not os.path.exists("data/chatchart"):
        print("Creating data/chatchart folder...")
        os.makedirs("data/chatchart")

def setup(bot):
    bot.add_cog(Meta(bot))
