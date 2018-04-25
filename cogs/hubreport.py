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

    async def member_ban(self, guild, user: discord.User):

        hubchannel=self.bot.get_channel(438710528299368458)

        try:

            embed = discord.Embed(color= 0xdf2a2a, title="🔨 Member Banned")
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text='Banned')
            embed.set_author(name=str(user.name), icon_url=user.avatar_url)
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
                    name="Banned by", value="Please enable access to AuditLogs to see this")

            await hubchannel.send(embed=embed)
        except Exception as e:
            await hubchannel.send(str(e))

def setup(bot: commands.Bot):
	n = HubReport(bot)
    bot.add_listener(n.member_ban, "on_member_ban")
	bot.add_cog(n)