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


	async def member_ban(self,guild,user: discord.User):

		reason = discord.utils.get(bans, user=user)[0]
		hubchannel=self.bot.get_channel(438710528299368458)
		try:
			embed = discord.Embed(title= "User Name: " + str(user.name) + " User ID: " + str(user.id),  colour=discord.Colour.red())
			embed.set_author(name= "🔨 User Action Report for " + str(user.name), icon_url=server.icon_url)
			embed.add_field(name= "Server:", value= server.name)
			embed.add_field(name= "Server ID: ", value = str(server.id))
			embed.add_field(name= "Reason: ", value= reason)
			embed.set_thumbnail(url=user.avatar_url)
			await hubchannel.send("Got This Far")
			await hubchannel.send(embed=embed)
		return
def setup(bot: commands.Bot):
	n = HubReport(bot)
	bot.add_listener(n.member_ban, "on_member_ban")
	bot.add_cog(n)