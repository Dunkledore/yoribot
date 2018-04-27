from copy import deepcopy
import os
import asyncio
import discord
from discord.ext import commands
import datetime
from .utils.dataIO import dataIO
from .utils import checks, time, chat_formatting as cf


class HubReport:

	"""Sends moderation information to the hub."""


	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.approve_emoji = "✅"
		self.reject_emoji = "❌"

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

			report = await hubchannel.send(embed=embed)
			await report.add_reaction(self.approve_emoji)
			await report.add_reaction(self.reject_emoji)
		except Exception as e:
			await hubchannel.send(str(e))

	@commands.command(hidden=True)
	async def addserver(self, ctx, channel: discord.TextChannel):
		"""Use this command to add your server to one of the disignated channels in the lgbtdiscord.com server."""

		if channel.id not in [438710892062965790, 438711271878033428, 438711230815797270, 438711168551354368]:
			await ctx.send("This is not a valid advertising channel")
			return

		def check(m):
			return (m.author is ctx.author) and (m.channel is ctx.channel)

		await ctx.send("Enter guild name")

		guild_name = (await self.bot.wait_for("message", check = check, timeout=300.0)).content
		await ctx.send("Enter guild description. Typing in notepad and pasting in will allow for multi-line")

		guild_description = (await self.bot.wait_for("message", check = check, timeout=300.0)).content

		await ctx.send("Send invite link")

		invite_link = (await self.bot.wait_for("message", check = check, timeout=300.0)).content

		await ctx.send("Link to server icon or logo.")

		icon_link = (await self.bot.wait_for("message", check = check, timeout=300.0)).content

		embed = discord.Embed(description = guild_description + "\n" + invite_link, title = guild_name)
		embed.set_thumbnail(url= icon_link)
		await channel.send(embed=embed)


	@commands.command(hidden=True)
	async def sendbans(self, ctx):
		"""Contribute to the safety of participating servers by uploading your ban information to our database."""
		if not self.audit_log_permissions(ctx.guild):
			await ctx.send(embed=self.bot.error("I don't have audit log permissions"))
			return

		all_bans = await ctx.guild.audit_logs(action=discord.AuditLogAction.ban).flatten()
		args = []
		for ban in all_bans:
			args.append((ban.target.id, ctx.guild.id, ban.reason, ctx.guild.name))

		query = "INSERT INTO bans VALUES ($1, $2, $3, $4)"
		await ctx.db.executemany(query, args)

		await ctx.send(embed=self.bot.success("Sent"))


	def audit_log_permissions(self, guild):
		member = guild.get_member(self.bot.user.id)
		return member.guild_permissions.view_audit_log


def setup(bot: commands.Bot):
	n = HubReport(bot)
	bot.add_listener(n.member_ban, "on_member_ban")
	bot.add_cog(n)