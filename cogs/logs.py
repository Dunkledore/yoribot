from discord.ext import commands
from .utils import checks, utils as yoriutils
from discord import TextChannel, Embed, Forbidden, utils, AuditLogAction
import asyncpg
import datetime
import asyncio


class Logs:

	def __init__(self, bot):
		self.bot = bot
		self.invites = {}

		if "Admin and Moderation" not in self.bot.categories:
			self.bot.categories["Admin and Moderation"] = [type(self).__name__]
		elif type(self).__name__ not in self.bot.categories["Admin and Moderation"]:
			self.bot.categories["Admin and Moderation"].append(type(self).__name__)

		self.bot.loop.create_task(self.track_invites())

	# Commands

	@commands.command()
	@checks.is_admin()
	async def start_message_logs(self, ctx, channel: TextChannel):

		insertquery = "INSERT INTO log_config (guild_id, message_log_channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE log_config SET message_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, ctx.guild.id, channel.id)

		await ctx.send(embed=self.bot.success(f'Now sending message logs to {channel.mention}. To stop sending message '
		                                      'logs, delete the channel '))

	@commands.command()
	@checks.is_admin()
	async def start_member_logs(self, ctx, channel: TextChannel):

		insertquery = "INSERT INTO log_config (guild_id, member_log_channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE log_config SET member_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, channel.id, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f'Now sending member logs to {channel.mention}. To stop sending message '
		                                      'logs, delete the channel '))

	@commands.command()
	@checks.is_admin()
	async def start_invite_logs(self, ctx, channel: TextChannel):

		insertquery = "INSERT INTO log_config (guild_id, invite_log_channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE log_config SET invite_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, ctx.guild.id, channel.id)

		await ctx.send(embed=self.bot.success(f'Now sending invite logs to {channel.mention}. To stop sending invite '
		                                      'logs, delete the channel '))

	@commands.command()
	@checks.is_mod()
	async def update_log(self, ctx, log_number : int, *, reason):
		query = "SELECT * from event_logs WHERE id = $1"
		report = await self.bot.pool.fetchrow(query, log_number)

		if not report:
			return await ctx.send(embed=self.bot.error("This is not a valid report"))

		if report["guild_id"] != ctx.guild.id:
			return await ctx.send(embed=self.bot.error("This report does not belong to this guild"))

		query = "UPDATE event_logs SET user_id = $1, reason = $2 WHERE id = $3"
		await self.bot.pool.execute(query, ctx.author.id, reason, log_number)
		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, ctx.guild.id)
		channel = self.bot.get_channel(log_channel_id)
		if not channel:
			return

		log_report_message = await channel.get_message(report["report_message_id"])
		if not log_report_message:
			return

		embed = log_report_message.embeds[0]
		for counter, field in enumerate(embed.fields):
			await ctx.send(str(field.name))
			if field.name in ["Banned by", "Unbanned by"]:
				embed.set_field_at(counter, name=field.name, value=ctx.author.mention)
				field.value = ctx.author.mention
			if field.name == "Reason":
				embed.set_field_at(counter, name="Reason", value=reason)
		await log_report_message.edit(embed=embed)



	# Events

	async def on_guild_channel_delete(self, channel):  # Kind of like and auto firing commands
		member_query = "UPDATE log_config SET member_log_channel_id = $1 WHERE member_log_channel_id = $2"
		message_query = "UPDATE log_config SET message_log_channel_id = $1 WHERE message_log_channel_id = $2"
		invite_query = "UPDATE log_config SET invite_log_channel_id = $1 WHERE invite_log_channel_id = $2"

		await self.bot.pool.execute(member_query, None, channel.id)
		await self.bot.pool.execute(message_query, None, channel.id)
		await self.bot.pool.execute(invite_query, None, channel.id)

	async def on_member_join(self, member):

		query = "INSERT into event_logs (action, target_id, user_id, guild_id) VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "join", member.id, None, member.guild.id)

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, member.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		created = (datetime.datetime.utcnow()-member.created_at).total_seconds()//60
		if created < 30:
			colour = 0xdda453
		else:
			colour = 0x53dda4

		embed = Embed(title=f'User Joined', colour=colour)
		embed.add_field(name="User", value=member.mention)
		embed.add_field(name="Username", value =f'{member.name}#{member.discriminator}')
		embed.add_field(name="User ID", value=f'{member.id}')

		embed.timestamp = datetime.datetime.utcnow()

		invites = await self.get_most_recent_used_invites_for_guild(member.guild)
		if not invites:
			invite_code = "Unknown"
			inviter = "Unknown"
			no_uses = "Unknown"
		else:
			invite_code = "\n".join([invite.code for invite in invites])
			inviter = "\n".join([invite.inviter.mention or "Widget" for invite in invites])
			no_uses = "\n".join([str(invite.uses) for invite in invites])
		embed.add_field(name='Invite', value=invite_code)
		embed.add_field(name="Inviter", value=inviter)
		embed.add_field(name="Number of invite uses", value=no_uses)

		try:
			self.invites[member.guild] = await member.guild.invites()
		except Forbidden:
			pass

		bans = await self.get_yori_bans(member)
		if bans:
			embed.colour = 0xdda453
			embed.add_field(name="Servers Banned In:", value="\n".join([guild.name for guild in bans]), inline=False)
		else:
			embed.add_field(name="Servers Banned In:", value="None", inline=False)

		query = "SELECT guild_id FROM log_config WHERE mod_participation = $1"
		participating_guilds = await self.bot.pool.fetch(query, True)
		participating_guilds = [participating_guild["guild_id"] for participating_guild in participating_guilds] + [0]
		query = f'SELECT DISTINCT guild_id FROM event_logs WHERE (target_id = $1) and (guild_id in {tuple(participating_guilds)})'
		guilds_id_with_logs = await self.bot.pool.fetch(query, member.id)
		guilds_with_logs = []
		for guild_id in guilds_id_with_logs:
			guild = self.bot.get_guild(guild_id["guild_id"])
			if guild:
				guilds_with_logs.append(guild)

		if guilds_with_logs:
			embed.add_field(name="Mod Logs", value="\n".join(
				[f'[{guild.name}]({self.bot.root_website}/logs/{guild.id}/{member.id})' for guild in guilds_with_logs]), inline=False)

		embed.add_field(name='Created', value=yoriutils.human_timedelta(member.created_at), inline=False)
		await log_channel.send(embed=embed)

	async def on_member_remove(self, member):

		query = "INSERT into event_logs (action, target_id, user_id, guild_id) VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "left", member.id, None, member.guild.id)

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, member.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'User Left', colour=0xFFA500)
		embed.add_field(name="User", value=member.mention)
		embed.add_field(name="Username", value =f'{member.name}#{member.discriminator}')
		embed.add_field(name="User ID", value=f'{member.id}')
		embed.timestamp = datetime.datetime.utcnow()
		embed.add_field(name='Was a member since', value=yoriutils.human_timedelta(member.joined_at), inline=False)
		await log_channel.send(embed=embed)

	async def on_member_ban(self, guild, user):

		query = "INSERT into event_logs (action, target_id, user_id, guild_id) VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "ban", user.id, None, guild.id)

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'User Banned - Mod Report #{log_id}', color=0xdf2a2a)
		embed.add_field(name="User", value=user.mention)
		embed.add_field(name="Username", value =f'{user.name}#{user.discriminator}')
		embed.add_field(name="User ID", value=f'{user.id}')
		embed.timestamp = datetime.datetime.utcnow()
		banner, reason = await self.get_ban_info(guild, user)
		embed.add_field(name="Banned by", value=banner.mention)
		embed.add_field(name="Reason", value=reason)

		embed.add_field(name="Message History",
		                value=f"[View Message History]({self.bot.root_website}/messages/{guild.id}/{user.id})\n[View Member Logs]({self.bot.root_website}/logs/{guild.id}/{user.id})")

		report_message = await log_channel.send(embed=embed)
		query = "UPDATE event_logs SET user_id = $1, reason = $2, report_message_id = $3 WHERE id = $4"
		await self.bot.pool.execute(query, banner.id, reason, report_message.id, log_id)


	async def on_member_unban(self, guild, user):

		query = "INSERT into event_logs (action, target_id, user_id, guild_id) VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "unban", user.id, None, guild.id)

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'Unbanned Banned - Mod Report #{log_id}', color=0xdf2a2a)
		embed.add_field(name="User", value=user.mention)
		embed.add_field(name="Username", value =f'{user.name}#{user.discriminator}')
		embed.add_field(name="User ID", value=f'{user.id}')

		embed.timestamp = datetime.datetime.utcnow()
		query = "SELECT user_id, reason FROM event_logs WHERE (action = $1) and (target_id = $2) and (guild_id = $3) ORDER BY id DESC LIMIT 1"
		ban_info = await self.bot.pool.fetchrow(query, "ban", user.id, guild.id)
		banner = self.bot.get_user(ban_info["user_id"])
		reason = ban_info["reason"]
		embed.add_field(name="Originally banned by", value=banner.mention if banner else f"User with id: {ban_info['user_id']}")
		embed.add_field(name="Original ban reason", value=reason)
		unbanner, unbanreason = await self.get_unban_info(guild, user)
		embed.add_field(name="Unbanned by", value=unbanner.mention)
		embed.add_field(name="Reason", value=unbanreason)

		report_message = await log_channel.send(embed=embed)
		query = "UPDATE event_logs SET user_id = $1, reason = $2, report_message_id = $3 WHERE id = $4"
		await self.bot.pool.execute(query, unbanner.id, unbanreason, report_message.id, log_id)

	async def on_message_delete(self, message):
		query = "UPDATE message_logs SET status = $1 WHERE message_id = $2"
		await self.bot.pool.execute(query, "deleted", message.id)

		query = "SELECT message_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, message.channe.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'Message Removed')
		embed.add_field(name="User", value=message.author.mention)
		embed.add_field(name="User Name", value=f'{message.author.name}{message.author.discriminator}')
		embed.add_field(name="User ID", value=f'{message.author.id}')
		embed.add_field(name="Channel", value=f'{message.channel.mention}')
		embed.add_field(name="Channel ID", value=f'{message.channel.id}')
		embed.add_field(name="Message Content", value=message.content)
		embed.timestamp = datetime.datetime.utcnow()

		await log_channel.send(embed=embed)

	async def on_message_edit(self, before, after):
		if self.bot.user in [before.author, after.author]:
			return
		query = "UPDATE message_logs SET status = $1, content = $2 WHERE message_id = $3"
		await self.bot.pool.execute(query, "edited", after.content, after.id)

		query = "SELECT message_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, before.channel.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'Message Edited')
		embed.add_field(name="User", value=after.author.mention)
		embed.add_field(name="User Name", value=f'{after.author.name}{after.author.discriminator}')
		embed.add_field(name="User ID", value=f'{after.author.id}')
		embed.add_field(name="Channel", value=f'{after.channel.mention}')
		embed.add_field(name="Channel ID", value=f'{after.channel.id}')
		if before.content:
			embed.add_field(name="Original Message Content", value=before.content, inline=False)
		if after.content:
			embed.add_field(name="New Message Content", value=after.content, inline=False)
		embed.timestamp = datetime.datetime.utcnow()

		await log_channel.send(embed=embed)

	# Utilities

	async def get_most_recent_used_invites_for_guild(self, guild):
		try:
			most_recent_used_invites = []
			previous_invites = self.invites.get(guild)
			if previous_invites:
				current_invites = await guild.invites()
				for new_invite in current_invites:
					previous_invite = utils.get(previous_invites, code=new_invite.code)
					if previous_invite:
						if previous_invite.uses < new_invite.uses:
							most_recent_used_invites.append(new_invite)
					elif new_invite.uses > 0:
						most_recent_used_invites.append(new_invite)

			return most_recent_used_invites
		except Forbidden:
			return []

	async def get_yori_bans(self, user):
		banned_in = []
		for guild in self.bot.guilds:
			try:
				bans = await guild.bans()
				for banentry in bans:
					if user == banentry[1]:
						banned_in.append(guild)
			except Forbidden:
				pass
		return banned_in

	async def track_invites(self):
		await self.bot.wait_until_ready()

		while True:
			for guild in self.bot.guilds:
				try:
					self.invites[guild] = await guild.invites()
				except Forbidden:
					pass
			await asyncio.sleep(60)

	async def get_ban_info(self, guild, user):
		try:
			timestamp = datetime.datetime.utcnow()
			bans_info = None
			ban_info = None
			while True:
				bans_info = await guild.audit_logs(action=AuditLogAction.ban).flatten()
				ban_info = utils.get(bans_info, target=user)
				if ban_info:
					if (timestamp-ban_info.created_at) <= datetime.timedelta(minutes=1):
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
			return banner, reasonbanned
		except Forbidden:
			return "No access to Audit Logs", "No access to Audit Logs"

	async def get_unban_info(self, guild, user):
		try:
			timestamp = datetime.datetime.utcnow()
			unbans_info = None
			unban_info = None
			while True:
				unbans_info = await guild.audit_logs(action=AuditLogAction.unban).flatten()
				unban_info = utils.get(unbans_info, target=user)
				if unban_info:
					if (timestamp-unban_info.created_at) <= datetime.timedelta(minutes=1):
						break
				else:
					asyncio.sleep(1)
			unbanner = unban_info.user
			if unbanner == guild.me:
				reasonunbanned = unban_info.reason
			else:
				if unban_info.reason:
					reasonunbanned = "{}".format(
						unban_info.reason)
				else:
					reasonbanned = "No Reason Provided"
			return unbanner, reasonunbanned
		except Forbidden:
			return "No access to Audit Logs", "No access to Audit Logs"

	# Temporary to for events

	@commands.command()
	@checks.is_developer()
	async def fake(self, ctx, event):
		if event == "on_member_join":
			func = getattr(self, "on_member_join")
			await func(ctx.author)
		if event == "on_member_remove":
			func = getattr(self, "on_member_remove")
			await func(ctx.author)
		if event == "on_member_ban":
			func = getattr(self, "on_member_ban")
			await func(ctx.guild, ctx.author)



def setup(bot):
	bot.add_cog(Logs(bot))
