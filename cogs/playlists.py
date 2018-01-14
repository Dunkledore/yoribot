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


class Playlists:

	def __init__(self,bot):
		self.playlist=[]
		self.context=None
	
	#def playlist_exists(self,userID,name):
	
	async def create_playlist(self,userID,name):
		query = "INSERT INTO playlists (userid,name,songs) VALUES ($1,$2,$3);"
		placeholder=''
		await self.context.db.execute(query, userID, name, placeholder)
	
	async def get_playlist(self,userID,name):
		query = "SELECT * FROM playlist WHERE userid = $1 AND name = $2;"
		result = await self.context.db.fetch(query, userID, name)
		
		self.playlist=result[0]["songs"].split(",")
		
	def save_playlist(self,userID,name):
	
		
		self.playlist=[]
	
	def check_query(self,query):
		url=urlparse(query)
		if url and url.scheme and url.netloc:
			return True
		else:
			return False

	def add_to_playlist(self,userID,name,front):
		
		async get_playlist(userID,name)
		if not check_query(query):
			return
		
		yt_videos = api_youtube.parse_query(query, self.statuslog)
		if front:
			self.playlist = yt_videos + self.playlist
		else:
			self.playlist = self.playlist + yt_videos
		self.context.send(str(self.playlist))
	
	#def remove_from_playlist(self,userID,name)
	
	#async def send_help(self,ctx):
	
	#def rename_playlist(self,name,userID,new_name):
	
			
	@commands.command()		
	async def playlist(self,ctx,command,playlist,*inputs):
		self.context=ctx
		if command.lower() == 'add':
			if not playlist_exists(ctx.message.author.id,playlist):
				await create_playlist(ctx.message.author.id,playlist)
			
			front=False
			if 'front' in inputs:
				front=True
				inputs = inputs[:-1]
			for item in inputs:
				add_to_playlist(ctx.message.author.id,playlist,front)
		
		elif command.lower() == 'remove':
		
		elif command.lower() == 'delete':
		
		elif command.lower() == 'rename':
		
def setup(bot):
    bot.add_cog(Playlists(bot))	