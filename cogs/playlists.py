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
		query = "INSERT INTO playlists (userid,name,songs) VALUES ($1,$2);"
		#placeholder=''
		await self.context.db.execute(query, userID, name)
	
	async def get_playlist(self,userID,name):
		self.list=[]
		query = "SELECT * FROM playlists WHERE userid = $1 AND name = $2;"
		result = await self.context.db.fetch(query, userID, name)
		
		self.list=result[0]["songs"].split(",")
		
	def save_playlist(self,userID,name):
	
		
		self.list=[]
	
	def check_query(self,query):
		url=urlparse(query)
		if url and url.scheme and url.netloc:
			return True
		else:
			return False

	async def add_to_playlist(self,userID,name,query,front=False):
		#await self.get_playlist(userID,name)
		yt_videos = api_youtube.parse_query(query, self.statuslog)
		if front:
			self.list = yt_videos + self.list
		else:
			self.list = self.list + yt_videos
		
	

	#def remove_from_playlist(self,userID,name)
	
	#async def send_help(self,ctx):
	
	#def rename_playlist(self,name,userID,new_name):
	
			
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
				await ctx.send("---")
				await self.add_to_playlist(ctx.message.author.id,name,item,front)
			await self.context.send(str(self.list))
		
		#elif command.lower() == 'remove':
		
		#elif command.lower() == 'delete':
		
		#elif command.lower() == 'rename':
	
def setup(bot):
    bot.add_cog(Playlists(bot))	