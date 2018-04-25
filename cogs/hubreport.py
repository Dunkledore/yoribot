from copy import deepcopy
import os

import discord
import datetime
from discord.ext import commands
from .utils.maxlist import MaxList
from .utils.dataIO import dataIO
from .utils import checks, time, chat_formatting as cf


class HubReport:

	"""Sends moderation information to the hub."""


	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.deletedmessages = MaxList(500)

	async def on_message_delete(self, message):
		self.deletedmessages.append(message)

		hubchannel=self.bot.get_channel(438710528299368458)
		he = discord.Embed(colour=discord.Colour.red())
		he.add_field(name='Message: ' + str(message.id), value= message.content, inline=False)
		he.set_footer(text=""'Sent In: ' + message.channel.name + ' Channel ID:  ' + str(message.channel.id))
		await hubchannel.send(embed=he)

	async def hub_ban_audit(self,guild,user: discord.User):

		server = guild
		bannedin= ""
		for guild in self.bot.guilds:
			try:
				bans = await guild.bans()
				for banentry in bans:
					if user == banentry[1]:
						bannedin += guild.name + '\n'
			except Exception as e:
				pass

			reason = discord.utils.get(bans, user=user)[0]
			hubchannel=self.bot.get_channel(438710528299368458)
		try:
			embed = discord.Embed(title= "User Name: " + str(user.name) + " User ID: " + str(user.id),  colour=discord.Colour.red())
			embed.set_author(name= "🔨 User Action Report for " + str(user.name), icon_url=server.icon_url)
			embed.add_field(name= "Server:", value= server.name)
			embed.add_field(name= "Server ID: ", value = str(server.id))
			embed.add_field(name= "Reason: ", value= reason)
			messages = gather_proof(user)
			for message in messages:
				embed.add_field(name= message.created_at, value= message.content)
			embed.set_thumbnail(url=user.avatar_url)

			if bannedin:
				embed.add_field(name='Banned In', value = bannedin, inline=False)
			await hubchannel.send(embed=embed)
		except Exception as e:
			await hubchannel.send(e)


def setup(bot: commands.Bot):
	n = HubReport(bot)
	bot.add_listener(n.hub_ban_audit, "on_member_ban")
	bot.add_cog(n)