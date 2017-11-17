import logging
import discord
from discord.ext import commands
from .utils import checks, formats

from .utils import datatools
from .music import _data, _musicplayer


class Music:

	def __init__(self,bot):
		self.bot = bot

	async def is_mod(self, user, channel, * , check=all):
		is_owner = await self.bot.is_owner(user)
		if is_owner:
			return True
		perms = {'manage_guild': True}
		resolved = channel.permissions_for(user)
		return check(getattr(resolved, name, None) == value for name, value in perms.items())

	def has_majority(self, reaction):
		listeners = len(reaction.message.guild.voice_client.channel.members)
		return (reaction.count-1) > (listeners-1/2)

	async def on_reaction_add(self, reaction, user):
		"""The on_message event handler for this module

		Args:
			reaction (discord.Reaction): Input reaction
			user (discord.User): The user that added the reaction
		"""

		# Simplify reaction info
		server = reaction.message.guild
		channel = reaction.message.channel
		emoji = reaction.emoji


		# Commands section
		if user != reaction.message.channel.guild.me:
			valid_reaction = (reaction.message.id) == _data.cache[str(server.id)].embed.sent_embed.id

			if valid_reaction:
				# Remove reaction			
				# Commands
				if emoji == "⏯":
					await _data.cache[str(server.id)].toggle()
				if emoji == "⏹":
					await _data.cache[str(server.id)].stop()
				if emoji == "⏭":
					is_mod = await self.is_mod(user, reaction.message.channel)
					has_majority = self.has_majority(reaction)
					if is_mod or has_majority:
						await _data.cache[str(server.id)].skip("1")
				if emoji == "🔀":
					is_mod = await self.is_mod(user, reaction.message.channel)
					if is_mod:
						await _data.cache[str(server.id)].shuffle()
				if emoji == "🔉":
					await _data.cache[str(server.id)].setvolume('-')
				if emoji == "🔊":
					await _data.cache[str(server.id)].setvolume('+')

	async def on_message(self, message):
		"""The on_message event handler for this module

		Args:
			message (discord.Message): Input message
		"""

		# Simplify message info
		server = message.guild
		author = message.author
		channel = message.channel
		content = message.content


		# Only reply to server messages and don't reply to myself
		if server is not None and author != channel.guild.me:
			# Commands section
			prefixes = tuple(self.bot.get_guild_prefixes(message.guild))
			for prefix in prefixes:
				if content.startswith(prefix):
					# Parse message
					package = content.split(" ")
					command = package[0][len(prefix):]
					args = package[1:]
					arg = ' '.join(args)

					# Lock on to server if not yet locked
					if str(server.id) not in _data.cache or _data.cache[str(server.id)].state == 'destroyed':
						_data.cache[str(server.id)] = _musicplayer.MusicPlayer(str(server.id), self.bot)

					# Remove message
					if command in ['play', 'playnext', 'playnow', 'pause', 'resume', 'skip', 'shuffle', 'volume', 'stop',
								   'destroy', 'front', 'movehere']:
						try:
							await message.delete()
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
						is_mod = await self.is_mod(message.author, message.channel )
						if is_mod:
							await _data.cache[str(server.id)].skip(query=arg)

					elif command == 'shuffle':
						is_mod = await self.is_mod(message.author, message.channel )
						if is_mod:
							await _data.cache[str(server.id)].shuffle()
					elif command == 'stop':
						await _data.cache[str(server.id)].stop()

					elif command == 'destroy':
						await _data.cache[str(server.id)].destroy()

					elif command == 'volume':
						await _data.cache[str(server.id)].setvolume(arg)

					elif command == 'front' or command == 'movehere':
						await _data.cache[str(server.id)].movehere(channel)
					return

def setup(bot):

	if datatools.has_data():
		data = datatools.get_data()
	else:
		# Create a blank data file
		data = {"discord": {}}

	if "keys" not in data["discord"]:
		data["discord"]["keys"] = {}

	if "google_api_key" not in data["discord"]["keys"]:
		data["discord"]["keys"]["google_api_key"] = 'AIzaSyB10j5t3LxMpuedlExxcVvj0rsezTurY9w'
		datatools.write_data(data)


	n = Music(bot)
	bot.add_cog(n)