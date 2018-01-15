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
		self.bot = bot
		self.list=[]
		self.playlist_list=[]
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
	
	async def get_playlist_list(self,userID):
		await self.context.send("getlist called")
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
		await self.context.send("save called")
		query = "UPDATE playlists SET Songs = $3, No_Songs = $4 WHERE userid=$1 AND name = $2"
		songs=self.convert_to_storage(self.list)
		await self.context.db.execute(query, userID, name, songs, len(self.list))
		
		
		self.list=[]
		
	
	def check_query(self,query):
		url=urlparse(query)
		if url and url.scheme and url.netloc:
			return True
		else:
			return False

	async def add_to_playlist(self,userID,name,query,front=False):
		if not await self.playlist_exists(userID,name):
			await self.create_playlist(userID,name)
		await self.context.send("add called")
		await self.get_playlist(userID,name)
		yt_videos = api_youtube.parse_query(query, self.statuslog)
		if front:
			self.list = yt_videos + self.list
		else:
			self.list = self.list + yt_videos
		
		await self.save_playlist(userID,name)
		return len(yt_videos)
	
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
		
		await self.save_playlist(userID,name)
		return counter
		
		
	async def delete_playlist(self,userID,name):
		await self.context.send("delete called")
		query = "DELETE FROM playlists WHERE userid=$1 AND name=$2;"
		await self.context.db.execute(query, userID, name)
		
		message="Playlist \"{}\" has been successfully deleted".format(name)
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="Success!",value=message)
		await self.context.channel.send(embed=embed)
		
	async def send_list(self,ctx):
		await ctx.send("sendlist called")
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
		await ctx.send("hi")
		self.context=ctx
		if not playlistname or urls==():
			ctx.send("Invalid Syntax")
			help_cmd = self.bot.get_command('help')
			await ctx.invoke(help_cmd, command=ctx.command.name)
			return
		urls=list(urls)
		front=False
		if 'front' in urls:
			front=True
			urls = urls[:-1]
			
		added_videos=0
		for item in urls:

			if not self.check_query(item):
				await self.send_error_message(ctx,"\"{}\" is not a valid input. Valid inputs are Youtube video and playlist URLs".format(item))
				continue
			added_videos+= await self.add_to_playlist(ctx.message.author.id,playlistname,item,front)
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="Done!",value="Added {} videos to the playlist \"{}\"".format(added_videos,playlistname))
		await ctx.send(embed=embed)
	
	@commands.command()	
	async def playlistremove(self,ctx,playlistname=None,*urls):
		self.context=ctx
		if not playlistname or urls==():
			ctx.send("Invalid Syntax")
			help_cmd = self.bot.get_command('help')
			await ctx.invoke(help_cmd, command=ctx.command.name)
			return
		urls=list(urls)
		if not await self.playlist_exists(ctx.message.author.id,playlistname):
			await ctx.send("Playlist \"{}\" does not exist".format(playlistname))
			await self.send_list(ctx)
			return
		
		deleted_videos=0
		for item in urls:
			if not self.check_query(item):
				await self.send_error_message(ctx,"\"{}\" is not a valid input. Valid inputs are Youtube video and playlist URLs".format(item))
				continue
			deleted_videos+=await self.remove_from_playlist(ctx.message.author.id,playlistname,item)
		embed=discord.Embed(title="", colour=discord.Colour.blurple())
		embed.add_field(name="Done!",value="Deleted {} videos from the playlist \"{}\"".format(deleted_videos,playlistname))
		await ctx.send(embed=embed)
	
	
	@commands.command()
	async def deleteplaylist(self,ctx,playlistname=None):
		self.context=ctx
		if not playlistname:
			ctx.send("Invalid Syntax")
			help_cmd = self.bot.get_command('help')
			await ctx.invoke(help_cmd, command=ctx.command.name)
		if not await self.playlist_exists(ctx.message.author.id,playlistname):
			await ctx.send("Playlist \"{}\" does not exist".format(playlistname))
			await self.send_list(ctx)
			return
		await self.delete_playlist(ctx.message.author.id,playlistname)
		
	@commands.command()	
	async def listplaylists(self,ctx):
		self.context=ctx
		await self.send_list(ctx)

	
def setup(bot):
    bot.add_cog(Playlists(bot))	