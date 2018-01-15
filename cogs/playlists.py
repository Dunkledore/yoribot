from .music import api_youtube
from .utils import db, checks, formats, cache

from urllib.parse import urlparse
from discord.ext import commands
import discord
import asyncio
import traceback
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)


class Playlists:

	def __init__(self,bot):
		self.list=[]
		self.context=None
		self.statuslog = logging.getLogger("{}.{}.status".format(__name__, 0))

	async def playlist_exists(self,userID,name):
		await self.context.send("exists called")
		query = "SELECT * FROM playlists WHERE userid = $1 AND name = $2;"
		result = await self.context.db.fetch(query, userID, name)
		if result:
			return True
		else:
			return False
	
	
	async def create_playlist(self,userID,name):
		await self.context.send("create called")
		query = "INSERT INTO playlists (userid,name) VALUES ($1,$2);"
		await self.context.db.execute(query, userID, name)
	
	async def get_playlist(self,userID,name):
		await self.context.send("get called")
		self.list=[]
		query = "SELECT * FROM playlists WHERE userid = $1 AND name = $2;"
		result = await self.context.db.fetch(query, userID, name)
		
		if result[0]["songs"]:
			self.list=self.convert_from_storage(result[0]["songs"])
		return self.list
		
	async def save_playlist(self,userID,name):
		await self.context.send("save called")
		query = "UPDATE playlists SET Songs = $3, No_Songs = $4 WHERE userid=$1 AND name = $2"
		songs=self.convert_to_storage(self.list)
		await self.context.db.execute(query, userID, name, songs, len(self.list))
		
		embed=discord.Embed(title="Playlist \"{}\" Successfully Updated!".format(name), colour=discord.Colour.blurple())
		summary.add_field(name="No. of Videos:",value=len(self.list))
		await ctx.channel.send(embed=embed)
		
		self.list=[]
		
	
	def check_query(self,query):
		url=urlparse(query)
		if url and url.scheme and url.netloc:
			return True
		else:
			return False

	async def add_to_playlist(self,userID,name,query,front=False):
		await self.context.send("add called")
		await self.get_playlist(userID,name)
		yt_videos = api_youtube.parse_query(query, self.statuslog)
		if front:
			self.list = yt_videos + self.list
		else:
			self.list = self.list + yt_videos
		
		await self.save_playlist(userID,name)
	
	def convert_to_storage(self,input):
		return json.dumps(input)
		
	
	def convert_from_storage(self,input):
		return json.loads(input)
	
	async def remove_from_playlist(self,userID,name,query):
		await self.context.send("remove called")
		await self.get_playlist(userID,name)
		yt_videos = api_youtube.parse_query(query, self.statuslog)
		initiallength=len(self.list)
		for video in yt_videos:
			if video in self.list:
				self.list=[value for value in self.list if value != video]
		finallength=len(self.list)
		counter=initiallength-finallength
		if counter == 0:
			await self.context.send("No Such Video")
		else:
			message=str(counter)+" videos deleted"
			await self.context.send(message)
			
		
		await self.save_playlist(userID,name)
		
	async def delete_playlist(self,userID,name):
		await self.context.send("delete called")
		query = "DELETE FROM playlists WHERE userid=$1 AND name=$2;"
		await self.context.db.execute(query, userID, name)
		
		message="Playlist {} has been successfully deleted".format(name)
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		summary.add_field(name="Success!",value=message)
		await self.context.channel.send(embed=embed)

	async def send_help(self,ctx):
		help=discord.Embed(title="", colour=discord.Colour.blurple())
		summary.add_field(name="Invalid Syntax",value = "Use \"{}help playlist\" for list of possible commands".format(ctx.prefix))
		await ctx.channel.send(embed=help)
		
	async def send_list(self,ctx):
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		summary.add_field(name="ERROR",value=message)
		await ctx.channel.send(embed=embed)
			
	@commands.command()
	async def playlist(self,ctx,command,playlistname,*inputs):
		self.context=ctx
		inputs=list(inputs)
		if command.lower() == 'add':
			if not await self.playlist_exists(ctx.message.author.id,playlistname):
				await self.create_playlist(ctx.message.author.id,playlistname)
			
			front=False
			if 'front' in inputs:
				front=True
				inputs = inputs[:-1]
			for item in inputs:
				if not self.check_query(item):
					#Error message sending#
					message="{} is not a valid input. Valid inputs are Youtube video and Playlist URLs".format(item)
					embed=discord.Embed(title="", colour=discord.Colour.blurple())
					summary.add_field(name="ERROR",value=message)
					await ctx.channel.send(embed=embed)
					#######################
					continue
				await self.add_to_playlist(ctx.message.author.id,playlistname,item,front)
			await self.context.send(str(self.list))
		
		elif command.lower() == 'remove':
			if not await self.playlist_exists(ctx.message.author.id,playlistname):
				#Error message sending#
				message="Playlist \"{}\" does not exist".format(playlistname)
				embed=discord.Embed(title="", colour=discord.Colour.blurple())
				summary.add_field(name="ERROR",value=message)
				await ctx.channel.send(embed=embed)
				#######################
				return
			for item in inputs:
				if not self.check_query(item):
					#Error message sending#
					message="{} is not a valid input. Valid inputs are Youtube video and Playlist URLs".format(item)
					embed=discord.Embed(title="", colour=discord.Colour.blurple())
					summary.add_field(name="ERROR",value=message)
					await ctx.channel.send(embed=embed)
					#######################
					continue
				await self.remove_from_playlist(ctx.message.author.id,playlistname,item)
		
		elif command.lower() == 'delete':
			if not await self.playlist_exists(ctx.message.author.id,playlistname):
				#Error message sending#
				message="Playlist \"{}\" does not exist".format(playlistname)
				embed=discord.Embed(title="", colour=discord.Colour.blurple())
				summary.add_field(name="ERROR",value=message)
				await ctx.channel.send(embed=embed)
				#######################
				return
			await self.delete_playlist(ctx.message.author.id,playlistname)
		elif command.lower() == 'list':
			await self.send_list(ctx)
		else:
			await self.send_help(ctx)

	
def setup(bot):
    bot.add_cog(Playlists(bot))	