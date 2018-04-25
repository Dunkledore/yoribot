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
		self.approve_emoji = "✅"
		self.reject_emoji = "❌"
		self.deletedmessages = MaxList(500)

	async def member_ban(self, guild, user: discord.User):

		hubchannel=self.bot.get_channel(438710528299368458)
		server = guild

		try:

			embed = discord.Embed(color= 0xdf2a2a)
			embed.timestamp = datetime.datetime.utcnow()
			embed.set_footer(text='Report Dated:')
			embed.set_author(name=str(user.name) + "was banned in" + server.name , icon_url=server.icon_url)
			embed.add_field(name='ID', value=str(user.id))
			embed.set_thumbnail(url= user.avatar_url)
			if self.audit_log_permissions(guild):
				timestamp = datetime.datetime.utcnow()
				bans_info = None
				ban_info = None
				while True:
					bans_info = await guild.audit_logs(action=discord.AuditLogAction.ban).flatten()
					ban_info = discord.utils.get(bans_info, target=user)
					if ban_info:
						if (timestamp - ban_info.created_at) <= datetime.timedelta(minutes=1):
							break
					else:
						asyncio.sleep(1)
				banner = ban_info.user
				if banner == guild.me:
					reasonbanned = ban_info.reason
				else:
					if ban_info.reason:
						reasonbanned = "{}".format(
							ban_info.reason)
					else:
						reasonbanned = "No Reason Provided"
				embed.add_field(name="Banned by:",
								value=banner.name)
				embed.add_field(name="Reason:",
								value=reasonbanned)
			else:
				embed.add_field(
					name="Error:", value="This server did not enable Audit Logs")
			messages = gather_proof(user)
			for message in messages:
				embed.add_field(name= message.created_at, value= message.content)

			report = await hubchannel.send(embed=embed)
			await report.add_reaction(self.approve_emoji)
			await report.add_reaction(self.reject_emoji)
		except Exception as e:
			await hubchannel.send(str(e))


	def audit_log_permissions(self, guild):
		member = guild.get_member(self.bot.user.id)
		return member.guild_permissions.view_audit_log

	def gather_proof(self,message):
		
		summary=[]
		for message in self.deletedmessage:
			if message.author == user:
				summary.append(message)
		return summary[-5:]


def setup(bot: commands.Bot):
	n = HubReport(bot)
	bot.add_listener(n.member_ban, "on_member_ban")
	bot.add_cog(n)