import logging

import discord

from modis import datatools
from . import _data, _musicplayer

logger = logging.getLogger(__name__)


async def on_message(message):
    """The on_message event handler for this module

    Args:
        message (discord.Message): Input message
    """

    # Simplify message info
    server = message.guild
    author = message.author
    channel = message.channel
    content = message.content

    data = datatools.get_data()

    if not data["discord"]["servers"][str(server.id)][_data.modulename]["activated"]:
        return

    # Only reply to server messages and don't reply to myself
    if server is not None and author != channel.server.me:
        # Commands section
        prefix = data["discord"]["servers"][str(server.id)]["prefix"]
        if content.startswith(prefix):
            # Parse message
            package = content.split(" ")
            command = package[0][len(prefix):]
            args = package[1:]
            arg = ' '.join(args)

            # Lock on to server if not yet locked
            if str(server.id) not in _data.cache or _data.cache[str(server.id)].state == 'destroyed':
                _data.cache[server.id] = _musicplayer.MusicPlayer(str(server.id))

            # Remove message
            if command in ['play', 'playnext', 'playnow', 'pause', 'resume', 'skip', 'shuffle', 'volume', 'stop',
                           'destroy', 'front', 'movehere']:
                try:
                    await self.bot.delete_message(message)
                except discord.errors.NotFound:
                    logger.warning("Could not delete music player command message - NotFound")
                except discord.errors.Forbidden:
                    logger.warning("Could not delete music player command message - Forbidden")

            # Commands
            if command == 'play':
                await _data.cache[str(server.id)].play(author, channel, arg)

            if command == 'playnext':
                await _data.cache[str(server.id)].play(author, channel, arg, now=True)

            if command == 'playnow':
                await _data.cache[str(server.id)].play(author, channel, arg, now=True, stop_current=True)

            elif command == 'pause':
                await _data.cache[str(server.id)].pause()

            elif command == 'resume':
                await _data.cache[str(server.id)].resume()

            elif command == 'skip':
                await _data.cache[str(server.id)].skip(query=arg)

            elif command == 'shuffle':
                await _data.cache[str(server.id)].shuffle()

            elif command == 'stop':
                await _data.cache[str(server.id)].stop()

            elif command == 'destroy':
                await _data.cache[str(server.id)].destroy()

            elif command == 'volume':
                await _data.cache[str(server.id)].setvolume(arg)

            elif command == 'front' or command == 'movehere':
                await _data.cache[str(server.id)].movehere(channel)
