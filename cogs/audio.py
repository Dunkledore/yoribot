import logging
import discord
from discord.ext import commands
from .utils import checks, formats

from .utils import datatools
from .music import _data, _musicplayer


class Music:

	def __init__(self,bot):
		self.bot = bot

	def has_majority(self, reaction):
		listeners = len(reaction.message.guild.voice_client.channel.members)
		return (reaction.count-1) > ((listeners-1)/2)

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
			print(type(reaction.message.id))
			print(type(_data.cache[str(server.id)].embed.sent_embed.id))
			valid_reaction = (reaction.message.id) == _data.cache[str(server.id)].embed.sent_embed.id

			if valid_reaction:
				is_mod = await self.is_mod(user, reaction.message.channel)
				has_majority = self.has_majority(reaction)
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
			return _musicplayer.MusicPlayer(str(server_id), self.bot)
		else:
			return _data.cache[str(server_id)]


	@commands.command(no_pm=True)
	async def play(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).play(ctx.author, ctx.channel, query)


	@commands.command(no_pm=True)
	@checks.is_mod()
	async def playnext(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).play(ctx.author, ctx.channel, query, now=True)

	@commands.command(no_pm=True, aliases=['movehere'])
	async def front(self, ctx):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).movehere(ctx.channel)


	@commands.command(no_pm=True)
	@checks.is_mod()
	async def playnow(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).play(ctx.author, ctx.channel, query, now=True, stop_current=True)

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def pause(self, ctx):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).pause()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def resume(self, ctx):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).resume()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def skip(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).skip(query=query)
		await ctx.send("skipped")

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def shuffle(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).shuffle()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def stop(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).stop()


	@commands.command(no_pm=True)
	@checks.is_mod()
	async def destroy(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).destroy()

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def volume(self, ctx, *, query=None):
		await ctx.message.delete()
		await self.getMusicPlayer(ctx.guild.id).setvolume(query)

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