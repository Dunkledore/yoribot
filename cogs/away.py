from discord.ext import commands
import discord
import asyncio
import asyncpg
import time


class Away:
	
	def __init__(self,bot):
	
		self.awaydata={}	
		
	def make_away(self,user,awaymessage):
	#create an entry in memory for said user including their id and message
		self.awaydata[user.id]={"message":awaymessage,"lastmessages":{},"awaymessages":[]}
	
	
	def create_summary(self,user):
	#creates and returns the embed summary of what the user will have missed
		summary=discord.Embed(title="Here's what you missed while you were gone:", colour=discord.Colour.blurple())
		
		
		for message in self.awaydata[user.id]["awaymessages"]:
			senderinfo=message["timestamp"] + ": " + message["author"] + " in " + message["channel"]
			content=message["content"]
			if message["attachments"]:
				for attachment in message["attachments"]:
					content=content + "\n " + attachment
			summary.add_field(name=senderinfo, value= content)
	
		return summary
	
	async def send_summary(self,user):
	#pms the user their summary 
		await user.send(embed=self.create_summary(user))
	
	def record_message(self,user,message):
	#stores message under that user's id
		attachmentlist=[]
		for attachment in message.attachments:
			attachmentlist.append(attachment.url)
			
		self.awaydata[user.id]["awaymessages"].append({"author":message.author.nick,"timestamp":message.created_at.strftime("%a %H:%M:%S"),"channel":message.channel.name,"content":message.content,"attachments":attachmentlist})

	def is_away(self, user):
	#checks if a user is away
		if user.id in self.awaydata:
			return True
		else:
			return False
	
	async def unmake_away(self,user):
	#deletes users file entry and sends their summary
	
		await self.send_summary(user)
		del self.awaydata[user.id]
	
	async def send_away_message(self,user,channel):
		#some embed saying that the bloke is away
		embed=discord.Embed(title=' ', colour=discord.Colour.blurple())
		embed.add_field(name=user.nick+' is currently away', value="I'll deliver him your message when he gets back")
		message = await channel.send(embed=embed)
		await self.replace_message(user,message,channel)
		
	async def replace_message(self,user,message,channel):
		if channel.id in away_data[user.id]["lastmessages"]:
			await away_data[user.id]["lastmessages"][channel.id].delete()
		away_data[user.id]["lastmessages"][channel.id]=message

	@commands.command()
	async def away(self, ctx, *, awaymessage):
		await ctx.message.delete()
		
		user=ctx.message.author
		
		if not self.is_away(user):
			self.make_away(user,awaymessage)
			embed=discord.Embed(title=' ', colour=discord.Colour.blurple())
			embed.add_field(name='You are now away', value= awaymessage)
			await ctx.send(embed=embed)
		else:
			#send something saying he's already away
			embed=discord.Embed(title=' ', colour=discord.Colour.blurple())
			embed.add_field(name='You are already away', value="Use '*back' command in order to return")
			await ctx.send(embed=embed)
	
	@commands.command()
	async def back(self, ctx):
		await ctx.message.delete()
		
		user=ctx.message.author
		
		if self.is_away(user):
			await self.unmake_away(user)
			embed=discord.Embed(title=' ', colour=discord.Colour.blurple())
			embed.add_field(name='Welcome Back', value=ctx.author.nick or ctx.author.name)
			await ctx.send(embed=embed)
		else:
			return
				
	async def on_message(self, message):
		
		if message.mention_everyone:
			for user in message.channel.members:
				if self.is_away(user):
					self.record_message(user,message)
			return
		
		if message.mentions:
			counter=0
			for user in message.mentions:
				if self.is_away(user):
					self.record_message(user,message)
					self.send_away_message(user)
					counter+=1	
					self.send_away_message(user,message.channel)
					
			if counter == len(message.mentions) and not message.attachments:
				await message.delete()
def setup(bot):
    bot.add_cog(Away(bot))