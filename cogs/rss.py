import discord
from discord.ext import commands
import os
import aiohttp
import asyncio
import string
import logging
import copy
from .utils import checks

from cogs.utils.dataIO import fileIO
from cogs.utils.chat_formatting import *

try:
    import feedparser
except:
    feedparser = None

log = logging.getLogger("red.rss")


class Settings(object):
    pass


class Feeds(object):
    def __init__(self):
        self.check_folders()
        # {guild:{channel:{name:,url:,last_scraped:,template:}}}
        self.feeds = fileIO("data/RSS/feeds.json", "load")

    def save_feeds(self):
        fileIO("data/RSS/feeds.json", "save", self.feeds)

    def check_folders(self):
        if not os.path.exists("data/RSS"):
            print("Creating data/RSS folder...")
            os.makedirs("data/RSS")
        self.check_files()

    def check_files(self):
        f = "data/RSS/feeds.json"
        if not fileIO(f, "check"):
            print("Creating empty feeds.json...")
            fileIO(f, "save", {})

    def update_time(self, guild, channel, name, time):
        if guild in self.feeds:
            if channel in self.feeds[guild]:
                if name in self.feeds[guild][channel]:
                    self.feeds[guild][channel][name]['last'] = time
                    self.save_feeds()

    async def edit_template(self, ctx, name, template):
        guild = ctx.message.guild.id
        channel = ctx.message.channel.id
        if guild not in self.feeds:
            return False
        if channel not in self.feeds[guild]:
            return False
        if name not in self.feeds[guild][channel]:
            return False
        self.feeds[guild][channel][name]['template'] = template
        self.save_feeds()
        return True

    def add_feed(self, ctx, name, url):
        guild = ctx.message.guild.id
        channel = ctx.message.channel.id
        if guild not in self.feeds:
            self.feeds[guild] = {}
        if channel not in self.feeds[guild]:
            self.feeds[guild][channel] = {}
        self.feeds[guild][channel][name] = {}
        self.feeds[guild][channel][name]['url'] = url
        self.feeds[guild][channel][name]['last'] = ""
        self.feeds[guild][channel][name]['template'] = "$name:\n$title"
        self.save_feeds()

    async def delete_feed(self, ctx, name):
        guild = ctx.message.guild.id
        channel = ctx.message.channel.id
        if guild not in self.feeds:
            return False
        if channel not in self.feeds[guild]:
            return False
        if name not in self.feeds[guild][channel]:
            return False
        del self.feeds[guild][channel][name]
        self.save_feeds()
        return True

    def get_feed_names(self, guild):
        if isinstance(guild, discord.guild):
            guild = guild.id
        ret = []
        if guild in self.feeds:
            for channel in self.feeds[guild]:
                ret = ret + list(self.feeds[guild][channel].keys())
        return ret

    def get_copy(self):
        return self.feeds.copy()


class RSS(object):
    def __init__(self, bot):
        self.bot = bot

        self.settings = Settings()
        self.feeds = Feeds()
        self.session = aiohttp.ClientSession()

    def __unload(self):
        self.session.close()

    def get_channel_object(self, channel_id):
        channel = self.bot.get_channel(channel_id)
        if channel and \
                channel.permissions_for(channel.guild.me).send_messages:
            return channel
        return None

    async def _get_feed(self, url):
        text = None
        try:
            with aiohttp.ClientSession() as session:
                with aiohttp.Timeout(3):
                    async with session.get(url) as r:
                        text = await r.text()
        except:
            pass
        return text

    async def valid_url(self, url):
        text = await self._get_feed(url)
        rss = feedparser.parse(text)
        if rss.bozo:
            return False
        else:
            return True

    @commands.group(pass_context=True, hidden=True)
    async def rss(self, ctx):
        """RSS feed stuff"""

    @rss.command(pass_context=True, name="add")
    @checks.is_admin()
    async def _rss_add(self, ctx, name: str, url: str):
        """Add an RSS feed to the current channel"""
        channel = ctx.message.channel
        valid_url = await self.valid_url(url)
        if valid_url:
            self.feeds.add_feed(ctx, name, url)
            await self.bot.send_message(
                channel,
                'Feed "{}" added. Modify the template using'
                ' rss template'.format(name))
        else:
            await self.bot.send_message(
                channel,
                'Invalid or unavailable URL.')

    @rss.command(pass_context=True, name="list")
    @checks.is_admin()
    async def _rss_list(self, ctx):
        """List currently running feeds"""
        msg = "Available Feeds:\n\t"
        msg += "\n\t".join(self.feeds.get_feed_names(ctx.message.guild))
        await ctx.send(box(msg))

    @rss.command(pass_context=True, name="template")
    @checks.is_admin()
    async def _rss_template(self, ctx, feed_name: str, *, template: str):
        ("""Set a template for the feed alert

        Each variable must start with $, valid variables:
        \tauthor, author_detail, comments, content, contributors, created,"""
         """ create, link, name, published, published_parsed, publisher,"""
         """ publisher_detail, source, summary, summary_detail, tags, title,"""
         """ title_detail, updated, updated_parsed""")
        template = template.replace("\\t", "\t")
        template = template.replace("\\n", "\n")
        success = await self.feeds.edit_template(ctx, feed_name, template)
        if success:
            await ctx.send("Template added successfully.")
        else:
            await ctx.send('Feed not found!')

    @rss.command(pass_context=True, name="force")
    @checks.is_admin()
    async def _rss_force(self, ctx, feed_name: str):
        """Forces a feed alert"""
        guild = ctx.message.guild
        channel = ctx.message.channel
        feeds = self.feeds.get_copy()
        if guild.id not in feeds:
            await ctx.send("There are no feeds for this guild.")
            return
        if channel.id not in feeds[guild.id]:
            await ctx.send("There are no feeds for this channel.")
            return
        if feed_name not in feeds[guild.id][channel.id]:
            await ctx.send("That feedname doesn't exist.")
            return

        items = copy.deepcopy(feeds[guild.id][channel.id][feed_name])
        items['last'] = ''

        message = await self.get_current_feed(guild.id, channel.id,
                                              feed_name, items)

        await ctx.send(message)

    @rss.command(pass_context=True, name="remove")
    @checks.is_admin()
    async def _rss_remove(self, ctx, name: str):
        """Removes a feed from this guild"""
        success = await self.feeds.delete_feed(ctx, name)
        if success:
            await ctx.send('Feed deleted.')
        else:
            await ctx.send('Feed not found!')

    async def get_current_feed(self, guild, chan_id, name, items):
        log.debug("getting feed {} on sid {}".format(name, guild))
        url = items['url']
        last_title = items['last']
        template = items['template']
        message = None

        try:
            async with self.session.get(url) as resp:
                html = await resp.read()
        except:
            log.exception("failure accessing feed at url:\n\t{}".format(url))
            return None

        rss = feedparser.parse(html)

        if rss.bozo:
            log.debug("Feed at url below is bad.\n\t".format(url))
            return None

        try:
            curr_title = rss.entries[0].title
        except IndexError:
            log.debug("no entries found for feed {} on sid {}".format(
                name, guild))
            return message

        if curr_title != last_title:
            log.debug("New entry found for feed {} on sid {}".format(
                name, guild))
            latest = rss.entries[0]
            to_fill = string.Template(template)
            message = to_fill.safe_substitute(
                name=bold(name),
                **latest
            )

            self.feeds.update_time(
                guild, chan_id, name, curr_title)
        return message

    async def read_feeds(self):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog('RSS'):
            feeds = self.feeds.get_copy()
            for guild in feeds:
                for chan_id in feeds[guild]:
                    for name, items in feeds[guild][chan_id].items():
                        log.debug("checking {} on sid {}".format(name, guild))
                        channel = self.get_channel_object(chan_id)
                        if channel is None:
                            log.debug("response channel not found, continuing")
                            continue
                        msg = await self.get_current_feed(guild, chan_id,
                                                          name, items)
                        if msg is not None:
                            await self.bot.send_message(channel, msg)
            await asyncio.sleep(300)


def setup(bot):
    if feedparser is None:
        raise NameError("You need to run `pip3 install feedparser`")
    n = RSS(bot)
    bot.add_cog(n)
    bot.loop.create_task(n.read_feeds())
