'''List of  possible errors:
name too long limit 255
playlist already exists cunt
not youtube link lelelelell
'''
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
		query = "SELECT * FROM playlists WHERE userid = $1 AND name = $2;"
		result = await self.context.db.fetch(query, userID, name)
		if result:
			return True
		else:
			return False
	
	
	async def create_playlist(self,userID,name):
		query = "INSERT INTO playlists (userid,name) VALUES ($1,$2);"
		await self.context.db.execute(query, userID, name)
	
	async def get_playlist(self,userID,name):
		self.list=[]
		query = "SELECT * FROM playlists WHERE userid = $1 AND name = $2;"
		result = await self.context.db.fetch(query, userID, name)
		
		self.list=self.convert_from_storage(result[0]["songs"])
		
	async def save_playlist(self,userID,name):
		query = "UPDATE playlists SET Songs = $3 WHERE userid=$1 AND name = $2"
		songs=self.convert_to_storage(self.list)
		await self.context.db.execute(query, userID, name, songs)
		
		self.list=[]
		
	
	def check_query(self,query):
		url=urlparse(query)
		if url and url.scheme and url.netloc:
			return True
		else:
			return False

	async def add_to_playlist(self,userID,name,query,front=False):
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
		
	async def delete_playlist(self,userID):
		query = "DELETE FROM playlists WHERE userid=$1 AND name=$2;"
		await self.context.db.execute(query, userID, name)
		#send message to say it's been deleted

	#async def send_help(self,ctx):
	
	
			
	@commands.command()
	async def playlist(self,ctx,command,name,*inputs):
		await ctx.send("hi")
		self.context=ctx
		inputs=list(inputs)
		if command.lower() == 'add':
			await ctx.send("command:add")
			if not await self.playlist_exists(ctx.message.author.id,name):
				await self.create_playlist(ctx.message.author.id,name)
			
			front=False
			if 'front' in inputs:
				front=True
				inputs = inputs[:-1]
			for item in inputs:
				if not self.check_query(item):
					continue
				await self.add_to_playlist(ctx.message.author.id,name,item,front)
			await self.context.send(str(self.list))
		
		elif command.lower() == 'remove':
			if not await self.playlist_exists(ctx.message.author.id,name):
				#say doesnt exists
				return
			for item in inputs:
				if not self.check_query(item):
					continue
				await self.remove_from_playlist(ctx.message.author.id,name,item)
		
		elif command.lower() == 'delete':
			if not await self.playlist_exists(ctx.message.author.id,name):
				#say doesnt exists
				return
			await delete_playlist(ctx.message.author.id,name)

	
def setup(bot):
    bot.add_cog(Playlists(bot))	