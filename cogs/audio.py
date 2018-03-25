import logging
import discord
from discord.ext import commands
from .utils import datatools
from .music import _data
from .music import _musicplayer
from .music import api_youtube
from .utils import db, checks, formats, cache
from urllib.parse import urlparse
import asyncio
import traceback
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)

def convert_to_storage(input):
	return json.dumps(input)
		
	
def convert_from_storage(input):
	return json.loads(input)
	
async def playlist_exists(ctx,name):
	"""
	The playlist_exists function:
	
	Checks wether or not a playlist exists with that name for the user in question

	Args:
		ctx(class): discord context class
		name(string): the name of the playlist to be returned
	"""
	userID=ctx.message.author.id
	query = "SELECT * FROM playlists WHERE userid = $1 AND name = $2;"
	result = await ctx.db.fetch(query, userID, name)
	if result:
		return True
	else:
		return False

async def get_playlist(ctx,name):
	"""
	The get_playlist function:

	Args:
		ctx(class): discord context class
		name(string): the name of the playlist to be returned
	Returns:
		list(list): playlist in the youtube API format [[url,name],[url,name],...]
	"""
	userID=ctx.message.author.id
	list=[]
	query = "SELECT * FROM playlists WHERE userid = $1 AND name = $2;"
	result = await ctx.db.fetch(query, userID, name)
	
	if result[0]["songs"]:
		list=convert_from_storage(result[0]["songs"])
	return list

class Playlists:
	"""Commands for creating and editing playlists that can be played using the music player"""

	def __init__(self,bot):
		self.bot = bot
		self.list=[]
		self.playlist_list=[]
		self.context=None
		self.statuslog = logging.getLogger("{}.{}.status".format(__name__, 0))
		self.silently_deleted=False
		self.catagory = "Personal Utility"
		
	async def create_playlist(self,userID,name):
		query = "INSERT INTO playlists (userid,name) VALUES ($1,$2);"
		await self.context.db.execute(query, userID, name)
	
	
	async def get_playlist_list(self,userID):
		query = "SELECT * FROM playlists WHERE userid = $1"
		results = await self.context.db.fetch(query, userID)
		self.playlist_list=[]
		if results:
			for column in results:
				self.playlist_list.append({"name":column["name"],"no_songs":column["no_songs"]})
		else:
			await self.send_error_message(self.context,"You currently have no playlists")
			return
			
		return 	
		
	async def save_playlist(self,userID,name):
		query = "UPDATE playlists SET Songs = $3, No_Songs = $4 WHERE userid=$1 AND name = $2"
		songs=convert_to_storage(self.list)
		await self.context.db.execute(query, userID, name, songs, len(self.list))
		
		
		self.list=[]
		
	
	def check_query(self,query):
		url=urlparse(query)
		if url and url.scheme and url.netloc:
			return True
		else:
			return False

	async def add_to_playlist(self,userID,name,query,front=False):
		if not await playlist_exists(self.context,name):
			await self.create_playlist(userID,name)
		self.list = await get_playlist(self.context,name)
		yt_videos = api_youtube.parse_query(query, self.statuslog)
		if front:
			self.list = yt_videos + self.list
		else:
			self.list = self.list + yt_videos
		
		await self.save_playlist(userID,name)
		return len(yt_videos)
	
	
	async def remove_from_playlist(self,userID,name,query):
		self.list = await get_playlist(self.context,name)
		yt_videos = api_youtube.parse_query(query, self.statuslog)
		initiallength=len(self.list)
		for video in yt_videos:
			self.list=[value for value in self.list if value[0] != video[0]]
		finallength=len(self.list)
		counter=initiallength-finallength
		await self.save_playlist(userID,name)
		if finallength==0:
			await self.delete_playlist(userID,name,True)
		return counter
		
		
	async def delete_playlist(self,userID,name,silent=False):
		query = "DELETE FROM playlists WHERE userid=$1 AND name=$2;"
		await self.context.db.execute(query, userID, name)
		
		if silent:
			self.silently_deleted=True
		else:
			message="Playlist \"{}\" has been successfully deleted".format(name)
			embed=discord.Embed(title="", colour=discord.Colour.blurple())
			embed.add_field(name="Success!",value=message)
			await self.context.channel.send(embed=embed)
		
	async def send_list(self,ctx):
		embed=discord.Embed(title="Here are your Playlists:", colour=discord.Colour.blurple())
		await self.get_playlist_list(ctx.message.author.id)
		if not self.playlist_list:
			return
		for i in self.playlist_list:
			embed.add_field(name=i["name"],value="{} Videos".format(i["no_songs"]))
		await ctx.channel.send(embed=embed)
	
	async def send_error_message(self,ctx,message):
		#Error message sending#
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="ERROR",value=message)
		await ctx.channel.send(embed=embed)
	
	@commands.command()
	async def playlistadd(self,ctx,playlistname=None,*urls):
		"""Used to add items to a playlist. Valid items are Youtube Video or Playlist URLs. If the playlist does not yet exist it will be created for you."""
		
		self.context=ctx
		if not playlistname or urls==():
			ctx.send("Invalid Syntax")
			help_cmd = self.bot.get_command('help')
			await ctx.invoke(help_cmd, command=ctx.command.name)
			return
		urls=list(urls)
		playlistname=playlistname.lower()
		front=False
		if 'front' in urls:
			front=True
			urls=[value for value in urls if value != 'front']
		
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="Working...",value="---")
		workmessage=await ctx.send(embed=embed)
		added_videos=0
		for item in urls:

			if not self.check_query(item):
				await self.send_error_message(ctx,"\"{}\" is not a valid input. Valid inputs are Youtube video and playlist URLs".format(item))
				continue
			added_videos+= await self.add_to_playlist(ctx.message.author.id,playlistname,item,front)
		await workmessage.delete()
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="Done!",value="Added {} videos to the playlist \"{}\"".format(added_videos,playlistname))
		await ctx.send(embed=embed)
	
	@commands.command()	
	async def playlistremove(self,ctx,playlistname=None,*urls):
		"""Used to remove all of said items from a playlist. Valid items are Youtube Video or Playlist URLs."""
		
		self.context=ctx
		if not playlistname or urls==():
			ctx.send("Invalid Syntax")
			help_cmd = self.bot.get_command('help')
			await ctx.invoke(help_cmd, command=ctx.command.name)
			return
		urls=list(urls)
		playlistname=playlistname.lower()
		if not await playlist_exists(ctx,playlistname):
			await ctx.send("Playlist \"{}\" does not exist".format(playlistname))
			await self.send_list(ctx)
			return
			
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="Working...",value="---")
		workmessage=await ctx.send(embed=embed)
	
		deleted_videos=0
		for item in urls:
			if not self.check_query(item):
				await self.send_error_message(ctx,"\"{}\" is not a valid input. Valid inputs are Youtube video and playlist URLs".format(item))
				continue
			if not self.silently_deleted:
				deleted_videos+=await self.remove_from_playlist(ctx.message.author.id,playlistname,item)
		await workmessage.delete()
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="Done!",value="Deleted {} videos from the playlist \"{}\"".format(deleted_videos,playlistname))
		await ctx.send(embed=embed)
		
	
	
	@commands.command(aliases=['playlistdelete'])
	async def deleteplaylist(self,ctx,playlistname=None):
		"""Used to delete a playlist"""
		
		self.context=ctx
		if not playlistname:
			ctx.send("Invalid Syntax")
			help_cmd = self.bot.get_command('help')
			await ctx.invoke(help_cmd, command=ctx.command.name)
		playlistname=playlistname.lower()
		if not await playlist_exists(ctx,playlistname):
			await ctx.send("Playlist \"{}\" does not exist".format(playlistname))
			await self.send_list(ctx)
			return
		await self.delete_playlist(ctx.message.author.id,playlistname)
		
	@commands.command(aliases=['playlistlist','playlistslist','listplaylist'])	
	async def listplaylists(self,ctx):
		"""Lists all of your playlists"""
		
		self.context=ctx
		await self.send_list(ctx)

class Music:
	"""A music player with an emoji controlled UI"""

	def __init__(self,bot):
		self.bot = bot
		self.counter={}
		self.catagory = "Personal Utility"

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


	@commands.command()
	@commands.guild_only()
	async def play(self, ctx, *, query=None):
		"""Play a song using its name or YouTube link or a playlist using its YouTube link."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).play(ctx.author, ctx.channel, query)


	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def playnext(self, ctx, *, query=None):
		"""Plays the song or playlist immediately after the track already playing"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).play(ctx.author, ctx.channel, query, now=True)

	@commands.command(aliases=['movehere'])
	@commands.guild_only()
	async def front(self, ctx):
		"""Brings the music player to the front of the chat"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).movehere(ctx.channel)


	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def playnow(self, ctx, *, query=None):
		"""Immediately plays the song - this will stop any song playing"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).play(ctx.author, ctx.channel, query, now=True, stop_current=True)

	@commands.command()
	@commands.guild_only()
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

	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def skip(self, ctx, *, query=1):
		"""Moves forward to the next song in the player queue."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).skip(query=query)
		await ctx.send("skipped")

	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def shuffle(self, ctx):
		"""Mixes the songs in the queue"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).shuffle()

	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def stop(self, ctx):
		"""Stops music playback."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).stop()


	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def destroy(self, ctx):
		"""Ends the music session - will clear all items from queue."""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).destroy()

	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def volume(self, ctx, *, query=None):
		"""Increase or decrease the volume"""
		await ctx.message.delete()
		await self.getMusicPlayer(str(ctx.guild.id)).setvolume(query)
	
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		id=str(message.guild.id)
		if id in _data.cache and _data.cache[id].state != 'destroyed' and message.channel==_data.cache[id].mchannel:
					if id not in self.counter:
						self.counter[id]=0
					self.counter[id]+=1
						
					if self.counter[id]==11:
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
	bot.add_cog(Playlists(bot))
