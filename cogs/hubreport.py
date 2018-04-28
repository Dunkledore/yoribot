from copy import deepcopy
import os
import asyncio
import discord
from discord.ext import commands
import datetime
from .utils.dataIO import dataIO
from .utils import checks, time, chat_formatting as cf
import asyncpg


#create table hubconfig (approved_guilds bigint[]) 

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
			reasonbanned = None
			if self.audit_log_permissions(guild):
				timestamp = datetime.datetime.utcnow()
				bans_info = None
				ban_info = None
				while True: #Audit Logs have inconsistencies so this loop ensures we get the result. 
					bans_info = await guild.audit_logs(action=discord.AuditLogAction.ban).flatten()
					ban_info = discord.utils.get(bans_info, target=user)
					if ban_info:
						if (timestamp - ban_info.created_at) <= datetime.timedelta(minutes=1):
							break
					else:
						asyncio.sleep(1)
				banner = ban_info.user
				reasonbanned = ban_info.reason or "No Reason Provided"
				embed.add_field(name="Banned by:",
								value=banner.name)
				embed.add_field(name="Reason:",
								value=reasonbanned)
			else:
				embed.add_field(
					name="Error:", value="This server did not enable Audit Logs")

			
			approved_query = "SELECT approved_guilds FROM hubconfig"
			insert_query = "INSERT INTO bans (user_id, guild_id, guild_name, reason, approved) VALUES ($1, $2, $3, $4, $5)"
			approved_guilds = (await self.bot.pool.fetchrow(approved_query))["approved_guilds"]
			approved_guild = guild.id in approved_guilds

			embed.add_field(name="Status", value="Auto-Approved. (Trusted Server)" if approved_guild else "Waiting For Approval 0/3")
			report = await hubchannel.send(embed=embed)
			try:
				await self.bot.pool.execute(insert_query, user.id, guild.id, guild.name, reasonbanned, True if approved_guild else False)
			except asyncpg.UniqueViolationError:
				delete_query = "DELETE FROM bans WHERE (user_id = $1) and (guild_id = $2)"
				await self.bot.pool.execute(delete_query, user.id, guild.id)
				await self.bot.pool.execute(insert_query, user.id, guild.id, guild.name, reasonbanned, True if approved_guild else False)


			if not approved_guild:
				await report.add_reaction(self.approve_emoji)
				await report.add_reaction(self.reject_emoji)

				approval_count = 0
				while -3 < approval_count <3:

					def check(reaction, user):
						if user.bot:
							return False
						return (reaction.message.id == report.id) and (reaction.emoji == self.approve_emoji or reaction.emoji == self.reject_emoji)

					reaction, react_user = await self.bot.wait_for("reaction_add", check=check)
					vote_up = reaction.emoji == self.approve_emoji
					staff_approver = False
					for role in react_user.roles:
						if role.id == 439366293100167192:
							staff_approver = True
					if staff_approver:
						approval_count = 3 if vote_up else -3
					else:
						approval_count = approval_count + (1 if vote_up else -1)

					
					if approval_count >= 3:
						embed.set_field_at(len(embed.fields)-1, name="Status", value = "Approved by {}".format("Staff" if staff_approver else "Votes"))
						update_query = "UPDATE bans SET approved = $1 WHERE (user_id = $2) and (guild_id = $3)"
						await self.bot.pool.execute(update_query, True, user.id, guild.id)
					elif approval_count <=-3:
						embed.set_field_at(len(embed.fields)-1, name="Status", value = "Denied by {}".format("Staff" if staff_approver else "Votes"))
					else:
						embed.set_field_at(len(embed.fields)-1, name="Status", value = "Waiting For Approval {}/3".format(approval_count))


					await report.edit(embed=embed)







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

		query = "SELECT DISTINCT guild_id FROM bans WHERE guild_id == $1" #Prevent dupes
		results = await self.bot.pool.fetch(query, ctx.guild.id)
		if results:
			await ctx.send(embed=self.bot.error("Yori already has Ban data for this guild. If you believe this to be an error please contact one of the staff"))
			return


		if not self.audit_log_permissions(ctx.guild):
			await ctx.send(embed=self.bot.error("I don't have audit log permissions"))
			return

		all_bans = await ctx.guild.audit_logs(action=discord.AuditLogAction.ban).flatten()
		args = []
		temp_remove_dups = [] #This means we only get the latest entry. No dupes
		for ban in all_bans:
			if ban.target.id in temp_remove_dups:
				continue
			args.append((ban.target.id, ctx.guild.id, ban.reason, ctx.guild.name))
			temp_remove_dups.append(ban.target.id)

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