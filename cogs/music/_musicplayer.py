import asyncio
import logging
import random
import youtube_dl
import discord
from os.path import join

from . import _data, api_youtube
from ..utils import ui_embed

logger = logging.getLogger(__name__)
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
ytdl.params["outtmpl"] = join("music", ytdl.params["outtmpl"])

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, ytdl.extract_info, url)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                   data=data)

class MusicPlayer:
    def __init__(self, server_id, bot):
        """Locks onto a server for easy management of various UIs

        Args:
            server_id (str): The Discord ID of the server to lock on to
        """

        # Player variables
        self.server_id = server_id
        self.logger = logging.getLogger("{}.{}".format(__name__, self.server_id))

        # Voice variables
        self.vchannel = None
        self.vclient = None
        self.streamer = None
        self.queue = []
        self.volume = 20

        # Status variables
        self.mready = False
        self.vready = False
        self.state = 'off'

        # Gui variables
        self.mchannel = None
        self.embed = None
        self.queue_display = 9
        self.nowplayinglog = logging.getLogger("{}.{}.nowplaying".format(__name__, self.server_id))
        self.queuelog = logging.getLogger("{}.{}.queue".format(__name__, self.server_id))
        self.queuelenlog = logging.getLogger("{}.{}.queuelen".format(__name__, self.server_id))
        self.volumelog = logging.getLogger("{}.{}.volume".format(__name__, self.server_id))
        self.statuslog = logging.getLogger("{}.{}.status".format(__name__, self.server_id))
        self.statuslog.setLevel("DEBUG")
        self.statustimer = None
        self.bot = bot

    async def setup(self, author, text_channel):
        """
        The setup command

        Args:
            author (discord.Member): The member that called the command
            text_channel (discord.Channel): The channel where the command was called
        """
        if self.state == 'off':
            self.state = 'starting'
            # Init the music player
            await self.msetup(text_channel)
            # Connect to voice
            await self.vsetup(author)

            # Mark as 'ready' if everything is ok
            self.state = 'ready' if self.mready and self.vready else 'off'

    async def play(self, author, text_channel, query, now=False, stop_current=False):
        """
        The play command

        Args:
            author (discord.Member): The member that called the command
            text_channel (discord.Channel): The channel where the command was called
            query (str): The argument that was passed with the command
            now (bool): Whether to play next or at the end of the queue
            stop_current (bool): Whether to stop the currently playing song
        """
        await self.setup(author, text_channel)

        if self.state == 'ready':
            # Queue the song
            self.enqueue(query, now)

            if stop_current:
                if self.streamer:
                    self.streamer.stop()

            # Start playing if not yet playing
            if self.streamer is None:
                await self.vplay()

    async def stop(self):
        """The stop command"""

        self.logger.debug("stop command")
        self.state = 'stopping'

        self.nowplayinglog.info("---")
        self.statuslog.info("Stopping")

        self.vready = False

        try:
            self.streamer.stop()
        except:
            pass

        try:
            await self.vclient.disconnect()
        except Exception as e:
            logger.error(e)
            pass

        self.vclient = None
        self.vchannel = None
        self.streamer = None
        self.queue = []

        self.update_queue()

        self.nowplayinglog.info("---")
        self.statuslog.info("Stopped")
        self.state = 'off'

        if self.embed:
            await self.embed.usend()

    async def destroy(self):
        """Destroy the whole gui and music player"""

        self.logger.debug("destroy command")
        self.state = 'destroyed'

        self.nowplayinglog.info("---")
        self.statuslog.info("Destroying")

        self.mready = False
        self.vready = False

        try:
            self.streamer.stop()
        except:
            pass

        try:
            await self.vclient.disconnect()
        except Exception as e:
            logger.error(e)
            pass

        self.vclient = None
        self.vchannel = None
        self.streamer = None
        self.queue = []

        if self.embed:
            await self.embed.delete()
            self.embed = None

    async def toggle(self):
        """Toggles between paused and not paused command"""

        self.logger.debug("toggle command")

        if not self.state == 'ready':
            return

        try:
            if self.streamer.is_playing():
                self.statuslog.info("Paused")
                self.streamer.pause()
            else:
                self.statuslog.info("Playing")
                self.streamer.resume()
        except Exception as e:
            logger.error(e)
            pass

    async def pause(self):
        """Pauses playback if playing"""

        self.logger.debug("pause command")

        if not self.state == 'ready':
            return

        try:
            if self.streamer.is_playing():
                self.statuslog.info("Paused")
                self.streamer.pause()
        except Exception as e:
            logger.error(e)
            pass

    async def resume(self):
        """Resumes playback if paused"""

        self.logger.debug("toggle command")

        if not self.state == 'ready':
            return

        try:
            if not self.streamer.is_playing():
                self.statuslog.info("Playing")
                self.streamer.resume()
        except Exception as e:
            logger.error(e)
            pass

    async def skip(self, query="1"):
        """The skip command

        Args:
            query (int): The number of items to skip
        """

        if not self.state == 'ready':
            logger.debug("Trying to skip from wrong state '{}'".format(self.state))
            return

        if query == "":
            query = "1"
        elif query == "all":
            query = str(len(self.queue) + 1)

        try:
            num = int(query)
        except TypeError:
            self.statuslog.debug("Skip argument must be a number")
        except ValueError:
            self.statuslog.debug("Skip argument must be a number")
        else:
            self.statuslog.info("Skipping")

            for i in range(num - 1):
                try:
                    self.queue.pop(0)
                except IndexError:
                    pass

            self.vclient.stop()


    async def shuffle(self):
        """The shuffle command"""

        self.logger.debug("shuffle command")

        if not self.state == 'ready':
            return

        self.statuslog.debug("Shuffling")

        random.shuffle(self.queue)

        self.update_queue()
        self.statuslog.debug("Shuffled")

    async def setvolume(self, value):
        """The volume command

        Args:
            value (str): The value to set the volume to
        """

        self.logger.debug("volume command")

        if self.state != 'ready':
            return

        logger.debug("Volume command received")

        if value == '+':
            if self.volume < 100:
                self.statuslog.debug("Volume up")
                self.volume = (10 * (self.volume // 10)) + 10
                self.volumelog.info(str(self.volume))
                try:
                    self.streamer.volume = self.volume / 100
                except AttributeError:
                    pass
            else:
                self.statuslog.debug("Already at maximum volume")

        elif value == '-':
            if self.volume > 0:
                self.statuslog.debug("Volume down")
                self.volume = (10 * ((self.volume + 9) // 10)) - 10
                self.volumelog.info(str(self.volume))
                try:
                    self.streamer.volume = self.volume / 100
                except AttributeError:
                    pass
            else:
                self.statuslog.debug("Already at minimum volume")

        else:
            try:
                value = int(value)
            except ValueError:
                self.statuslog.debug("Volume argument must be +, -, or a %")
            else:
                if 0 <= value <= 200:
                    self.statuslog.debug("Setting volume")
                    self.volume = value
                    self.volumelog.info(str(self.volume))
                    try:
                        self.streamer.volume = self.volume / 100
                    except AttributeError:
                        pass
                else:
                    self.statuslog.debug("Volume must be between 0 and 200%")

    async def movehere(self, channel):
        """Moves the embed message to a new channel; can also be used to move the musicplayer to the front

        Args:
            channel (discord.Channel): The channel to move to
        """

        self.logger.debug("movehere command")

        # Delete the old message
        await self.embed.delete()
        # Set the channel to this channel
        self.embed.channel = channel
        # Send a new embed to the channel
        await self.embed.send()
        # Re-add the reactions
        await self.add_reactions()

        self.statuslog.info("Moved to front")

    # Methods
    async def vsetup(self, author):
        """Creates the voice client

        Args:
            author (discord.Member): The user that the voice ui will seek
        """

        if self.vready:
            logger.error("Attempt to init voice when already initialised")
            return

        if self.state != 'starting':
            logger.error("Attempt to init from wrong state ('{}'), must be 'starting'.".format(self.state))
            return

        self.logger.debug("Setting up voice")

        # Create voice client
        self.vchannel = author.voice.channel
        if self.vchannel:
            self.statuslog.info("Connecting to voice")
            try:
                self.vclient = await self.vchannel.connect()
            except discord.ClientException:
                self.statuslog.error("I'm already connected to a voice channel.")
                return
            except discord.DiscordException:
                self.statuslog.error("I couldn't connect to the voice channel. Check my permissions.")
                return
            except Exception as e:
                self.statuslog.error("Internal error connecting to voice, disconnecting")
                logger.error("Error connecting to voice {}".format(e))
                return
        else:
            self.statuslog.error("You're not connected to a voice channel.")
            return

        self.vready = True

    async def msetup(self, text_channel):
        """Creates the gui

        Args:
            text_channel (discord.Channel): The channel for the embed ui to run in
        """

        if self.mready:
            logger.error("Attempt to init music when already initialised")
            return

        if self.state != 'starting':
            logger.error("Attempt to init from wrong state ('{}'), must be 'starting'.".format(self.state))
            return

        self.logger.debug("Setting up gui")

        # Create gui
        self.mchannel = text_channel
        self.new_embed_ui()
        await self.embed.send()
        await self.embed.usend()
        await self.add_reactions()

        self.mready = True

    def new_embed_ui(self):
        """Create the embed UI object and save it to self"""

        self.logger.debug("Creating new embed ui object")

        # Initial queue display
        queue_display = []
        for i in range(self.queue_display):
            queue_display.append("{}: ---\n".format(str(i + 1)))

        # Initial datapacks
        datapacks = [
            ("Now playing", "---", False),
            ("Queue", "```{}```".format(''.join(queue_display)), False),
            ("Songs left in queue", "---", True),
            ("Volume", "{}%".format(self.volume), True),
            ("Status", "```---```", False)
        ]

        # Create embed UI object
        self.embed = ui_embed.UI(
            self.bot,
            self.mchannel,
            "Music Player",
            "Press the buttons!",
            modulename=_data.modulename,
            creator=_data.creator,
            colour=0x88FF00,
            datapacks=datapacks,
        )

        # Add handlers to update gui
        noformatter = logging.Formatter("{message}", style="{")
        codeformatter = logging.Formatter("```{message}```", style="{")
        volumeformatter = logging.Formatter("{message}%", style="{")

        nowplayinghandler = EmbedLogHandler(self, self.embed, 0, self.bot)
        nowplayinghandler.setFormatter(noformatter)
        queuehandler = EmbedLogHandler(self, self.embed, 1, self.bot)
        queuehandler.setFormatter(codeformatter)
        queuelenhandler = EmbedLogHandler(self, self.embed, 2, self.bot)
        queuelenhandler.setFormatter(noformatter)
        volumehandler = EmbedLogHandler(self, self.embed, 3, self.bot)
        volumehandler.setFormatter(volumeformatter)
        statushandler = EmbedLogHandler(self, self.embed, 4, self.bot)
        statushandler.setFormatter(codeformatter)

        self.nowplayinglog.addHandler(nowplayinghandler)
        self.queuelog.addHandler(queuehandler)
        self.queuelenlog.addHandler(queuelenhandler)
        self.volumelog.addHandler(volumehandler)
        self.statuslog.addHandler(statushandler)

    async def add_reactions(self):
        """Adds the reactions buttons to the current message"""
        self.statuslog.info("Loading buttons")
        for e in ("⏯", "⏹", "⏭", "🔀", "🔉", "🔊"):
            try:
                if self.embed is not None:
                    await self.embed.sent_embed.add_reaction(e)
                    print()
            except discord.DiscordException:
                self.statuslog.error("I couldn't add the buttons. Check my permissions.")
            except Exception as e:
                logger.exception(e)

    def enqueue(self, query, front=False):
        """Queues songs based on either a YouTube search or a link

        Args:
            query (str): Either a search term or a link
            front (bool): Whether to enqueue at the front or the end
        """

        if self.state != 'ready':
            logger.error("Attempt to queue song from wrong state ('{}'), must be 'ready'.".format(self.state))
            return

        self.logger.debug("Enqueueing from query")

        self.statuslog.info("Queueing {}".format(query))

        yt_videos = api_youtube.parse_query(query, self.statuslog)
        if front:
            self.queue = yt_videos + self.queue
        else:
            self.queue = self.queue + yt_videos

        self.update_queue()
        self.statuslog.info("Queued {}".format(query))

    def update_queue(self):
        """ Updates the queue in the music player """

        self.logger.debug("Updating queue display")

        queue_display = []
        for i in range(self.queue_display):
            try:
                if len(self.queue[i][1]) > 40:
                    songname = self.queue[i][1][:37] + "..."
                else:
                    songname = self.queue[i][1]
            except IndexError:
                songname = "---"
            queue_display.append("{}: {}\n".format(str(i + 1), songname))

        self.queuelog.info(''.join(queue_display))
        self.queuelenlog.info(str(len(self.queue)))

    async def vplay(self):
        
        def vafter_inside(self):
            self.vafter_ts()


        if self.state != 'ready':
            logger.error("Attempt to play song from wrong state ('{}'), must be 'ready'.".format(self.state))
            return

        self.state = "starting streamer"

        self.logger.debug("Playing next in queue")

        # Queue has items
        if self.queue:
            self.statuslog.info("Loading next song")

            song = self.queue[0][0]
            songname = self.queue[0][1]

            self.queue.pop(0)

            player = await YTDLSource.from_url(song, loop=self.bot.loop)
            self.streamer = player
            self.state = "ready"

            self.streamer.volume = self.volume / 100
            self.vclient.play(player, after=self.vafter_inside)

            self.statuslog.info("Playing")
            self.nowplayinglog.info(songname)
        else:
            self.statuslog.info("Finished queue")
            self.state = "ready"

            self.update_queue()

            await self.stop()

    def vafter_ts(self):
        print("LINE594")
        try:
            future = asyncio.run_coroutine_threadsafe(self.vafter(), self.bot.loop)
            print("LINE597")
        except Exception as e:
            print(e)
        try:
            future.result()
        except Exception as e:
            print(e) 

    async def vafter(self):
        """Function that is called after a song finishes playing"""

        self.logger.debug("Finished playing a song")
        if self.state != 'ready':
            self.logger.debug("Returning because player is in state {}".format(self.state))
            return

        try:
            if self.streamer.error is None:
                await self.vplay()
            else:
                await self.destroy()
                self.statuslog.error(self.streamer.error)
                self.statuslog.critical("Encountered an error while playing :/")
        except Exception as e:
            try:
                await self.destroy()
            except:
                pass

            logger.exception(e)


class EmbedLogHandler(logging.Handler):
    def __init__(self, music_player, embed, line, bot):
        """

        Args:
            embed (ui_embed.UI):
            line (int):
        """
        logging.Handler.__init__(self)

        self.music_player = music_player
        self.embed = embed
        self.line = line
        self.bot = bot

    def flush(self):
        try:
            asyncio.run_coroutine_threadsafe(self.usend_when_ready(), self.bot.loop)
        except Exception as e:
            return

    async def usend_when_ready(self):
        if self.embed is not None:
            await self.embed.usend()

    def emit(self, record):
        msg = self.format(record)
        try:
            self.embed.update_data(self.line, msg)
        except AttributeError:
            return
        self.flush()
