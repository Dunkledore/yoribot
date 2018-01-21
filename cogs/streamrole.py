from copy import deepcopy
import os
import os.path
import discord
from discord.ext import commands
from discord.utils import find
from .utils.dataIO import dataIO
from .utils import checks
from .utils import chat_formatting as cf
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils.chat_formatting import escape_mass_mentions
from collections import defaultdict
from string import ascii_letters
from random import choice
import re
import aiohttp
import asyncio
import logging


default_settings = {
    "enabled": False,
    "role": None
}

class StreamsError(Exception):
    pass


class StreamNotFound(StreamsError):
    pass


class APIError(StreamsError):
    pass


class InvalidCredentials(StreamsError):
    pass


class OfflineStream(StreamsError):
    pass


class StreamRole:

    """Assign a configurable role to anyone who is streaming."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_path = "data/streamrole/settings.json"
        self.settings = dataIO.load_json(self.settings_path)
        self.twitch_streams = dataIO.load_json("data/streamrole/twitch.json")
        self.hitbox_streams = dataIO.load_json("data/streamrole/hitbox.json")
        self.beam_streams = dataIO.load_json("data/streamrole/beam.json")
        streamsettings = dataIO.load_json("data/streamrole/streamsettings.json")
        self.streamsettings = defaultdict(dict, streamsettings)
        self.messages_cache = defaultdict(list)

    @commands.group(pass_context=True, no_pm=True, name="streamroleset")
    @checks.is_admin()
    async def _streamroleset(self, ctx):
        """Sets StreamRole settings."""

        guild = ctx.message.guild
        if str(str(guild.id)) not in self.settings:
            self.settings[str(str(guild.id))] = deepcopy(default_settings)
            dataIO.save_json(self.settings_path, self.settings)


    @_streamroleset.command(name="toggle")
    @commands.guild_only()
    @checks.is_admin()
    async def _toggle(self, ctx):
        """Toggles StreamRole on/off."""

        await ctx.message.channel.trigger_typing()

        guild = ctx.message.guild
        if (not self.settings[str(str(guild.id))]["enabled"] and
                self.settings[str(str(guild.id))]["role"] is None):
            await ctx.send(cf.warning(
                "You need to set the role before turning on StreamRole."
                " Use `{}streamroleset role`".format(ctx.prefix)))
            return

        self.settings[str(str(guild.id))]["enabled"] = not self.settings[str(str(guild.id))]["enabled"]
        if self.settings[str(str(guild.id))]["enabled"]:
            await ctx.send(
                cf.info("StreamRole is now enabled."))
        else:
            await ctx.send(
                cf.info("StreamRole is now disabled."))
        dataIO.save_json(self.settings_path, self.settings)

    @_streamroleset.command(name="role")
    @commands.guild_only()
    @checks.is_admin()
    async def _role(self, ctx, role: discord.Role):
        """Sets the role that StreamRole assigns to
        members that are streaming.
        """

        await ctx.message.channel.trigger_typing()

        guild = ctx.message.guild
        self.settings[str(str(guild.id))]["role"] = str(role.id)
        dataIO.save_json(self.settings_path, self.settings)

        await ctx.send(
            cf.info("Any member who is streaming will now be given the "
                    "role `{}`. Ensure you also toggle the cog on with "
                    "`{}streamroleset toggle`.".format(role.name, ctx.prefix)))

    async def stream_listener(self, before: discord.Member,
                              after: discord.Member):
        if str(before.str(guild.id)) not in self.settings:
            self.settings[str(before.str(guild.id))] = deepcopy(default_settings)
            dataIO.save_json(self.settings_path, self.settings)

        guild_settings = self.settings[str(before.str(guild.id))]
        if guild_settings["enabled"] and guild_settings["role"] is not None:
            streamer_role = find(lambda m: (str(m.id)) == guild_settings["role"],
                                 before.guild.roles)
            if streamer_role is None:
                return
            # is streaming
            if (after.game is not None and
                    after.game.type == 1 and
                    streamer_role not in after.roles):
                await after.add_roles(streamer_role)
            # is not
            elif ((after.game is None or after.game.type != 1) and
                  streamer_role in after.roles):
                await after.remove_roles(streamer_role)
    @commands.command()
    async def hitbox(self, ctx, stream: str):
        """Checks if hitbox stream is online"""
        stream = escape_mass_mentions(stream)
        regex = r'^(https?\:\/\/)?(www\.)?(hitbox\.tv\/)'
        stream = re.sub(regex, '', stream)
        try:
            embed = await self.hitbox_online(stream)
        except OfflineStream:
            await ctx.send(stream + " is offline.")
        except StreamNotFound:
            await ctx.send("That stream doesn't exist.")
        except APIError:
            await ctx.send("Error contacting the API.")
        else:
            await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def twitch(self, ctx, stream: str):
        """Checks if twitch stream is online"""
        stream = escape_mass_mentions(stream)
        regex = r'^(https?\:\/\/)?(www\.)?(twitch\.tv\/)'
        stream = re.sub(regex, '', stream)
        try:
            data = await self.fetch_twitch_ids(stream, raise_if_none=True)
            embed = await self.twitch_online(data[0]["_id"])
        except OfflineStream:
            await ctx.send(stream + " is offline.")
        except StreamNotFound:
            await ctx.send("That stream doesn't exist.")
        except APIError:
            await ctx.send("Error contacting the API.")
        except InvalidCredentials:
            await ctx.send("Owner: Client-ID is invalid or not set. "
                               "See `{}streamset twitchtoken`"
                               "".format(ctx.prefix))
        else:
            await ctx.send(embed=embed)

    @commands.command()
    async def beam(self, ctx, stream: str):
        """Checks if beam stream is online"""
        stream = escape_mass_mentions(stream)
        regex = r'^(https?\:\/\/)?(www\.)?(beam\.pro\/)'
        stream = re.sub(regex, '', stream)
        try:
            embed = await self.beam_online(stream)
        except OfflineStream:
            await ctx.send(stream + " is offline.")
        except StreamNotFound:
            await ctx.send("That stream doesn't exist.")
        except APIError:
            await ctx.send("Error contacting the API.")
        else:
            await ctx.send(embed=embed)

    @commands.group(pass_context=True, no_pm=True)
    @checks.is_mod()
    async def streamalert(self, ctx):
        """Adds/removes stream alerts from the current channel"""
        if ctx.invoked_subcommand is None:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='streamalert')
    
    @streamalert.command(name="twitch", pass_context=True)
    async def twitch_alert(self, ctx, stream: str):
        """Adds/removes twitch alerts from the current channel"""
        stream = escape_mass_mentions(stream)
        regex = r'^(https?\:\/\/)?(www\.)?(twitch\.tv\/)'
        stream = re.sub(regex, '', stream)
        channel = ctx.message.channel
        try:
            data = await self.fetch_twitch_ids(stream, raise_if_none=True)
        except StreamNotFound:
            await ctx.send("That stream doesn't exist.")
            return
        except APIError:
            await ctx.send("Error contacting the API.")
            return
        except InvalidCredentials:
            await ctx.send("Owner: Client-ID is invalid or not set. "
                               "See `{}streamset twitchtoken`"
                               "".format(ctx.prefix))
            return

        enabled = self.enable_or_disable_if_active(self.twitch_streams,
                                                   stream,
                                                   channel,
                                                   _id=data[0]["_id"])

        if enabled:
            await ctx.send("Alert activated. I will notify this channel "
                               "when {} is live.".format(stream))
        else:
            await ctx.send("Alert has been removed from this channel.")

        dataIO.save_json("data/streamrole/twitch.json", self.twitch_streams)

    @streamalert.command(name="hitbox", pass_context=True)
    async def hitbox_alert(self, ctx, stream: str):
        """Adds/removes hitbox alerts from the current channel"""
        stream = escape_mass_mentions(stream)
        regex = r'^(https?\:\/\/)?(www\.)?(hitbox\.tv\/)'
        stream = re.sub(regex, '', stream)
        channel = ctx.message.channel
        try:
            await self.hitbox_online(stream)
        except StreamNotFound:
            await ctx.send("That stream doesn't exist.")
            return
        except APIError:
            await ctx.send("Error contacting the API.")
            return
        except OfflineStream:
            pass

        enabled = self.enable_or_disable_if_active(self.hitbox_streams,
                                                   stream,
                                                   channel)

        if enabled:
            await ctx.send("Alert activated. I will notify this channel "
                               "when {} is live.".format(stream))
        else:
            await ctx.send("Alert has been removed from this channel.")

        dataIO.save_json("data/streamrole/hitbox.json", self.hitbox_streams)

    @streamalert.command(name="beam", pass_context=True)
    async def beam_alert(self, ctx, stream: str):
        """Adds/removes beam alerts from the current channel"""
        stream = escape_mass_mentions(stream)
        regex = r'^(https?\:\/\/)?(www\.)?(beam\.pro\/)'
        stream = re.sub(regex, '', stream)
        channel = ctx.message.channel
        try:
            await self.beam_online(stream)
        except StreamNotFound:
            await ctx.send("That stream doesn't exist.")
            return
        except APIError:
            await ctx.send("Error contacting the API.")
            return
        except OfflineStream:
            pass

        enabled = self.enable_or_disable_if_active(self.beam_streams,
                                                   stream,
                                                   channel)

        if enabled:
            await ctx.send("Alert activated. I will notify this channel "
                               "when {} is live.".format(stream))
        else:
            await ctx.send("Alert has been removed from this channel.")

        dataIO.save_json("data/streamrole/beam.json", self.beam_streams)

    @streamalert.command(name="stop", pass_context=True)
    async def stop_alert(self, ctx):
        """Stops all streams alerts in the current channel"""
        channel = ctx.message.channel

        streams = (
            self.hitbox_streams,
            self.twitch_streams,
            self.beam_streams
        )

        for stream_type in streams:
            to_delete = []

            for s in stream_type:
                if channel.id in s["CHANNELS"]:
                    s["CHANNELS"].remove(channel.id)
                    if not s["CHANNELS"]:
                        to_delete.append(s)

            for s in to_delete:
                stream_type.remove(s)

        dataIO.save_json("data/streamrole/twitch.json", self.twitch_streams)
        dataIO.save_json("data/streamrole/hitbox.json", self.hitbox_streams)
        dataIO.save_json("data/streamrole/beam.json", self.beam_streams)

        await ctx.send("There will be no more stream alerts in this "
                           "channel.")

    @commands.group(pass_context=True)
    async def streamset(self, ctx):
        """Stream settings"""
        if ctx.invoked_subcommand is None:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='streamset')

    @streamset.command()
    @checks.is_developer()
    async def twitchtoken(self, ctx, token: str = ""):
        """Sets the Client-ID for Twitch

        https://blog.twitch.tv/client-id-required-for-kraken-api-calls-afbb8e95f843"""
        if not token or len(token) < 30:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='streamset twitchtoken')
            return
        self.streamsettings["TWITCH_TOKEN"] = token
        dataIO.save_json("data/streamrole/streamsettings.json", self.streamsettings)
        await ctx.send('Twitch Client-ID set.')

    @streamset.command(pass_context=True, no_pm=True)
    @checks.is_admin()
    async def mention(self, ctx, *, mention_type : str):
        """Sets mentions for stream alerts

        Types: everyone, here, none"""
        guild = ctx.message.guild
        mention_type = mention_type.lower()

        if mention_type in ("everyone", "here"):
            self.streamsettings[str(str(guild.id))]["MENTION"] = "@" + mention_type
            await ctx.send("When a stream is online @\u200b{} will be "
                               "mentioned.".format(mention_type))
        elif mention_type == "none":
            self.streamsettings[str(guild.id)]["MENTION"] = ""
            await ctx.send("Mentions disabled.")
        else:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='mention')

        dataIO.save_json("data/streamrole/streamsettings.json", self.streamsettings)

    @streamset.command(pass_context=True, no_pm=True)
    @checks.is_admin()
    async def autodelete(self, ctx):
        """Toggles automatic notification deletion for streams that go offline"""
        guild = ctx.message.guild
        settings = self.streamsettings[str(guild.id)]
        current = settings.get("AUTODELETE", True)
        settings["AUTODELETE"] = not current
        if settings["AUTODELETE"]:
            await ctx.send("Notifications will be automatically deleted "
                               "once the stream goes offline.")
        else:
            await ctx.send("Notifications won't be deleted anymore.")

        dataIO.save_json("data/streamrole/streamsettings.json", self.streamsettings)

    async def hitbox_online(self, stream):
        url = "https://api.hitbox.tv/media/live/" + stream

        async with aiohttp.get(url) as r:
            data = await r.json(encoding='utf-8')

        if "livestream" not in data:
            raise StreamNotFound()
        elif data["livestream"][0]["media_is_live"] == "0":
            raise OfflineStream()
        elif data["livestream"][0]["media_is_live"] == "1":
            return self.hitbox_embed(data)

        raise APIError()

    async def twitch_online(self, stream):
        session = aiohttp.ClientSession()
        url = "https://api.twitch.tv/kraken/streams/" + stream
        header = {
            'Client-ID': self.streamsettings.get("TWITCH_TOKEN", ""),
            'Accept': 'application/vnd.twitchtv.v5+json'
        }

        async with session.get(url, headers=header) as r:
            data = await r.json(encoding='utf-8')
        await session.close()
        if r.status == 200:
            if data["stream"] is None:
                raise OfflineStream()
            return self.twitch_embed(data)
        elif r.status == 400:
            raise InvalidCredentials()
        elif r.status == 404:
            raise StreamNotFound()
        else:
            raise APIError()

    async def beam_online(self, stream):
        url = "https://beam.pro/api/v1/channels/" + stream

        async with aiohttp.get(url) as r:
            data = await r.json(encoding='utf-8')
        if r.status == 200:
            if data["online"] is True:
                return self.beam_embed(data)
            else:
                raise OfflineStream()
        elif r.status == 404:
            raise StreamNotFound()
        else:
            raise APIError()

    async def fetch_twitch_ids(self, *streams, raise_if_none=False):
        def chunks(l):
            for i in range(0, len(l), 100):
                yield l[i:i + 100]

        base_url = "https://api.twitch.tv/kraken/users?login="
        header = {
            'Client-ID': self.streamsettings.get("TWITCH_TOKEN", ""),
            'Accept': 'application/vnd.twitchtv.v5+json'
        }
        results = []

        for streams_list in chunks(streams):
            session = aiohttp.ClientSession()
            url = base_url + ",".join(streams_list)
            async with session.get(url, headers=header) as r:
                data = await r.json()
            if r.status == 200:
                results.extend(data["users"])
            elif r.status == 400:
                raise InvalidCredentials()
            else:
                raise APIError()
            await session.close()

        if not results and raise_if_none:
            raise StreamNotFound()

        return results

    def twitch_embed(self, data):
        channel = data["stream"]["channel"]
        url = channel["url"]
        logo = channel["logo"]
        if logo is None:
            logo = "https://static-cdn.jtvnw.net/jtv_user_pictures/xarth/404_user_70x70.png"
        status = channel["status"]
        if not status:
            status = "Untitled broadcast"
        embed = discord.Embed(title=status, url=url)
        embed.set_author(name=channel["display_name"])
        embed.add_field(name="Followers", value=channel["followers"])
        embed.add_field(name="Total views", value=channel["views"])
        embed.set_thumbnail(url=logo)
        if data["stream"]["preview"]["medium"]:
            embed.set_image(url=data["stream"]["preview"]["medium"] + self.rnd_attr())
        if channel["game"]:
            embed.set_footer(text="Playing: " + channel["game"])
        embed.color = 0x6441A4
        return embed

    def hitbox_embed(self, data):
        base_url = "https://edge.sf.hitbox.tv"
        livestream = data["livestream"][0]
        channel = livestream["channel"]
        url = channel["channel_link"]
        embed = discord.Embed(title=livestream["media_status"], url=url)
        embed.set_author(name=livestream["media_name"])
        embed.add_field(name="Followers", value=channel["followers"])
        #embed.add_field(name="Views", value=channel["views"])
        embed.set_thumbnail(url=base_url + channel["user_logo"])
        if livestream["media_thumbnail"]:
            embed.set_image(url=base_url + livestream["media_thumbnail"] + self.rnd_attr())
        embed.set_footer(text="Playing: " + livestream["category_name"])
        embed.color = 0x98CB00
        return embed

    def beam_embed(self, data):
        default_avatar = ("https://beam.pro/_latest/assets/images/main/"
                          "avatars/default.jpg")
        user = data["user"]
        url = "https://beam.pro/" + data["token"]
        embed = discord.Embed(title=data["name"], url=url)
        embed.set_author(name=user["username"])
        embed.add_field(name="Followers", value=data["numFollowers"])
        embed.add_field(name="Total views", value=data["viewersTotal"])
        if user["avatarUrl"]:
            embed.set_thumbnail(url=user["avatarUrl"])
        else:
            embed.set_thumbnail(url=default_avatar)
        if data["thumbnail"]:
            embed.set_image(url=data["thumbnail"]["url"] + self.rnd_attr())
        embed.color = 0x4C90F3
        if data["type"] is not None:
            embed.set_footer(text="Playing: " + data["type"]["name"])
        return embed

    def enable_or_disable_if_active(self, streams, stream, channel, _id=None):
        """Returns True if enabled or False if disabled"""
        for i, s in enumerate(streams):
            if s["NAME"] != stream:
                continue

            if channel.id in s["CHANNELS"]:
                streams[i]["CHANNELS"].remove(channel.id)
                if not s["CHANNELS"]:
                    streams.remove(s)
                return False
            else:
                streams[i]["CHANNELS"].append(channel.id)
                return True

        data = {"CHANNELS": [channel.id],
                "NAME": stream,
                "ALREADY_ONLINE": False}

        if _id:
            data["ID"] = _id

        streams.append(data)

        return True

    async def stream_checker(self):
        CHECK_DELAY = 60

        try:
            await self._migration_twitch_v5()
        except InvalidCredentials:
            print("Error during convertion of twitch usernames to IDs: "
                  "invalid token")
        except Exception as e:
            print("Error during convertion of twitch usernames to IDs: "
                  "{}".format(e))
        handler = logging.FileHandler(filename='test.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger = logging.getLogger()
        logger.addHandler(handler)
        while self == self.bot.get_cog("StreamRole"):
            logger.log("i'm in")
            
            save = False

            streams = ((self.twitch_streams, self.twitch_online),
                       (self.hitbox_streams, self.hitbox_online),
                       (self.beam_streams,   self.beam_online))

            for streams_list, parser in streams:
                if parser == self.twitch_online:
                    _type = "ID"
                else:
                    _type = "NAME"
                for stream in streams_list:
                    if _type not in stream:
                        continue
                    key = (parser, stream[_type])
                    try:
                        embed = await parser(stream[_type])
                    except OfflineStream:
                        if stream["ALREADY_ONLINE"]:
                            stream["ALREADY_ONLINE"] = False
                            save = True
                            await self.delete_old_notifications(key)
                    except:  # We don't want our task to die
                        continue
                    else:
                        if stream["ALREADY_ONLINE"]:
                            continue
                        save = True
                        stream["ALREADY_ONLINE"] = True
                        messages_sent = []
                        for channel_id in stream["CHANNELS"]:
                            channel = self.bot.get_channel(channel_id)
                            if channel is None:
                                continue
                            mention = self.streamsettings.get(channel.str(guild.id), {}).get("MENTION", "")
                            can_speak = channel.permissions_for(channel.guild.me).send_messages
                            message = mention + " {} is live!".format(stream["NAME"])
                            if channel and can_speak:
                                m = await self.bot.send_message(channel, message, embed=embed)
                                messages_sent.append(m)
                        self.messages_cache[key] = messages_sent

                    await asyncio.sleep(0.5)

            if save:
                dataIO.save_json("data/streamrole/twitch.json", self.twitch_streams)
                dataIO.save_json("data/streamrole/hitbox.json", self.hitbox_streams)
                dataIO.save_json("data/streamrole/beam.json", self.beam_streams)

            await asyncio.sleep(CHECK_DELAY)

    async def delete_old_notifications(self, key):
        for message in self.messages_cache[key]:
            guild = message.guild
            settings = self.streamsettings.get(str(guild.id), {})
            is_enabled = settings.get("AUTODELETE", True)
            try:
                if is_enabled:
                    await self.bot.delete_message(message)
            except:
                pass

        del self.messages_cache[key]

    def rnd_attr(self):
        """Avoids Discord's caching"""
        return "?rnd=" + "".join([choice(ascii_letters) for i in range(6)])

    async def _migration_twitch_v5(self):
        #  Migration of old twitch streams to API v5
        to_convert = []
        for stream in self.twitch_streams:
            if "ID" not in stream:
                to_convert.append(stream["NAME"])

        if not to_convert:
            return

        results = await self.fetch_twitch_ids(*to_convert)

        for stream in self.twitch_streams:
            for result in results:
                if stream["NAME"].lower() == result["name"].lower():
                    stream["ID"] = result["_id"]

        # We might as well delete the invalid / renamed ones
        self.twitch_streams = [s for s in self.twitch_streams if "ID" in s]

        dataIO.save_json("data/streamrole/twitch.json", self.twitch_streams)


def check_folders():
    if not os.path.exists("data/streamrole"):
        print("Creating data/streamrole folder...")
        os.makedirs("data/streamrole")
    if not os.path.exists("data/streamrole"):
        print("Creating data/streamrole directory...")
        os.makedirs("data/streamrole")

def check_files():
    stream_files = (
        "twitch.json",
        "hitbox.json",
        "beam.json"
    )

    for filename in stream_files:
        if not dataIO.is_valid_json("data/streamrole/" + filename):
            print("Creating empty {}...".format(filename))
            dataIO.save_json("data/streamrole/" + filename, [])

    f = "data/streamrole/streamsettings.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty streamsettings.json...")
        dataIO.save_json(f, {})
    g = "data/streamrole/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/streamrole/settings.json...")
        dataIO.save_json(g, {})

def setup(bot: commands.Bot):
    check_folders()
    check_files()
    logger = logging.getLogger('aiohttp.client')
    logger.setLevel(50)  # Stops warning spam
    n = StreamRole(bot)
    bot.add_listener(n.stream_listener, "on_member_update")
    loop = asyncio.get_event_loop()
    loop.create_task(n.stream_checker())
    bot.add_cog(n)
