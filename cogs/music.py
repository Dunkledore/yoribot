import logging
import discord 

from utils import datatools
from music import _data, _musicplayer

class Music:

	def __init__(self,bot):
		self.bot = bot

	async def on_reaction_add(reaction, user):
		"""The on_message event handler for this module

		Args:
			reaction (discord.Reaction): Input reaction
			user (discord.User): The user that added the reaction
		"""

		# Simplify reaction info
		server = reaction.message.guild
		channel = reaction.message.channel
		emoji = reaction.emoji

		data = datatools.get_data()

		if not data["discord"]["servers"][str(server.id)][_data.modulename]["activated"]:
			return

		# Commands section
		if user != reaction.message.channel.server.me:
			if server.id not in _data.cache or _data.cache[str(server.id)].state == 'destroyed':
				return

			try:
				valid_reaction = str(reaction.message.id) == _data.cache[str(server.id)].embed.sent_embed.id
			except AttributeError:
				pass
			else:
				if valid_reaction:
					# Remove reaction
					try:
						await self.bot.remove_reaction(reaction.message, emoji, user)
					except discord.errors.NotFound:
						pass
					except discord.errors.Forbidden:
						pass
						
					# Commands
					if emoji == "⏯":
						await _data.cache[str(server.id)].toggle()
					if emoji == "⏹":
						await _data.cache[str(server.id)].stop()
					if emoji == "⏭":
						await _data.cache[str(server.id)].skip("1")
					if emoji == "🔀":
						await _data.cache[str(server.id)].shuffle()
					if emoji == "🔉":
						await _data.cache[str(server.id)].setvolume('-')
					if emoji == "🔊":
						await _data.cache[str(server.id)].setvolume('+')


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


def setup(bot):
	n = Music(bot)
	bot.add_cog(n)