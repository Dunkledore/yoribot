import logging
import discord
from discord.ext import commands
from .utils import checks, formats

from .utils import datatools
from .music import _data, _musicplayer


class Music:

	def __init__(self,bot):
		self.bot = bot
		self.counter={}

	async def has_majority(self, reaction):
		listeners = len(reaction.message.guild.voice_client.channel.members)
		lisnener_reaction_count = 0
		reactioners = await reaction.users().flatten()
		for user in reactioners:
			if not user.voice:
				continue
			if user.voice.channel.id == reaction.message.guild.voice_client.channel.members:
				lisnener_reaction_count += 1

		return (lisnener_reaction_count) > ((listeners-1)/2)

	async def is_mod(self, user, channel, * , check=all):
		is_owner = await self.bot.is_owner(user)
		if is_owner:
			return True
		perms = {'manage_guild': True}
		resolved = channel.permissions_for(user)
		return check(getattr(resolved, name, None) == value for name, value in perms.items())

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
				is_mod = await self.is_mod(user, reaction.message.channel)
				has_majority = await self.has_majority(reaction)
				# Remove reaction			
				# Commands
				if is_mod or has_majority:
					if emoji == "⏯":
						await _data.cache[str(server.id)].toggle()
					if emoji == "⏹":
						await _data.cache[str(server.id)].stop()
					if emoji == "⏭":
							await _data.cache[str(server.id)].skip("1")
					if emoji == "🔀":
						await _data.cache[str(server.id)].shuffle()
						async for ruser in reaction.users():
							if ruser.id != self.bot.user.id:
								await reaction.message.remove_reaction(emoji, ruser)
					if emoji == "🔉":
						await _data.cache[str(server.id)].setvolume('-')
						async for ruser in reaction.users():
							if ruser.id != self.bot.user.id:
								await reaction.message.remove_reaction(emoji, ruser)
					if emoji == "🔊":
						await _data.cache[str(server.id)].setvolume('+')
						async for ruser in reaction.users():
							if ruser.id != self.bot.user.id:
								await reaction.message.remove_reaction(emoji, ruser)

	def getMusicPlayer(self, server_id):
		if str(server_id) not in _data.cache or _data.cache[str(server_id)].state == 'destroyed':
			_data.cache[str(server_id)] = _musicplayer.MusicPlayer(str(server_id), self.bot)
			return _data.cache[str(server_id)]
		else:
			return _data.cache[str(server_id)]


	@commands.command(no_pm=True)
	async def play(self, ctx, *, query=None):
		"""Play a song using its name or YouTube link or a playlist using its YouTube link."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).play(ctx.author, ctx.channel, query)


	@commands.command(no_pm=True)
	@checks.is_mod()
	async def playnext(self, ctx, *, query=None):
		"""Plays the song or playlist immediately after the track already playing"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).play(ctx.author, ctx.channel, query, now=True)

	@commands.command(no_pm=True, aliases=['movehere'])
	async def front(self, ctx):
		"""Brings the music player to the front of the chat"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).movehere(ctx.channel)


	@commands.command(no_pm=True)
	@checks.is_mod()
	async def playnow(self, ctx, *, query=None):
		"""Immediately plays the song - this will stop any song playing"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).play(ctx.author, ctx.channel, query, now=True, stop_current=True)

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def pause(self, ctx):
		"""Pauses the track currently playing"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).pause()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def resume(self, ctx):
		"""Resumes a paused track"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).resume()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def skip(self, ctx, *, query=1):
		"""Moves forward to the next song in the player queue."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).skip(query=query)
		await ctx.send("skipped")

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def shuffle(self, ctx):
		"""Mxes the songs in the queue"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).shuffle()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def stop(self, ctx):
		"""Stops music playback."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).stop()


	@commands.command(no_pm=True)
	@checks.is_mod()
	async def destroy(self, ctx):
		"""Ends the music session - will clear all items from queue."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).destroy()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def volume(self, ctx, *, query=None):
		"""Increase or decrease the volume"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).setvolume(query)
	
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		id=str(message.guild.id)
		await message.channel.send(str(self.counter))
		if id in _data.cache:
			await message.channel.send('i am in the cache')
			if _data.cache[id].state != 'destroyed' :
				await message.channel.send('i am not destroyed')
				if message.channel==_data.cache[id].mchannel:
					await message.channel.send('i am in the correct channel')
					self.counter[id]=self.counter[id]+1
					
					if self.counter[id]%5==0:
						self.counter[id]=0
						await self.getMusicPlayer(id).movehere(message.channel)

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