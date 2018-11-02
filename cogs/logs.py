from discord.ext import commands
from .utils import checks, utils as yoriutils
from discord import TextChannel, Embed, Forbidden, utils, AuditLogAction, Member, Object
import asyncpg
import datetime
import asyncio


class Logs:
	"""Commands related to logging of events"""

	def __init__(self, bot):
		self.bot = bot
		self.invites = {}

		self.category = "Admin and Moderation"

		self.black_listed_channels = []
		self.invite_task = self.bot.loop.create_task(self.track_invites())
		self.blacklist_task = self.bot.loop.create_task(self.update_blacklist_cache())

	def __unload(self):
		self.invite_task.cancel()
		self.blacklist_task.cancel()


	# Commands

	@commands.command()
	@checks.is_admin()
	async def start_message_logs(self, ctx, channel: TextChannel):
		"""Starts sending logs about message edits and deletes to the given channel"""

		insertquery = "INSERT INTO log_config (guild_id, message_log_channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE log_config SET message_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, channel.id, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f'Now sending message logs to {channel.mention}. To stop sending message '
		                                      'logs, delete the channel '))

	@commands.command()
	@checks.is_admin()
	async def start_member_logs(self, ctx, channel: TextChannel):
		"""Starts sending logs about member join, leaves, bans and unbans to the given channel. N.B. It will also send member mute information but only if the member was muted through Yori"""

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
		"""Starts sending logs about invite creations, deletion and expirations to the given channel"""

		insertquery = "INSERT INTO log_config (guild_id, invite_log_channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE log_config SET invite_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, channel.id, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f'Now sending invite logs to {channel.mention}. To stop sending invite '
		                                      'logs, delete the channel '))

	@commands.command()
	@checks.is_admin()
	async def start_strike_logs(self, ctx, channel: TextChannel):
		"""Starts sending logs about member strikes to the given channel. N.B. Strikes must be setup from within Automod before any logs will be send"""

		insertquery = "INSERT INTO log_config (guild_id, strike_log_channel_id) VALUES ($1, $2)"
		alterquery = "UPDATE log_config SET strike_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, channel.id, ctx.guild.id)

		await ctx.send(embed=self.bot.success(f'Now sending strikes logs to {channel.mention}. To stop sending strike '
		                                      'logs, delete the channel '))

	@commands.command()
	@checks.is_mod()
	async def warn(self, ctx, member : Member, reason):
		query = "INSERT into event_logs (action, target_id, user_id, guild_id, reason) VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "warn", member.id, ctx.author.id, ctx.guild.id, reason)

		await ctx.message.add_reaction("\N{Thumbs Up Sign}")

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, member.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'User Warned - Mod Report #{log_id}')  #TODO Colour
		embed.add_field(name="User", value=member.mention)
		embed.add_field(name="Username", value =f'{member.name}#{member.discriminator}')
		embed.add_field(name="User ID", value=f'{member.id}')
		embed.add_field(name="Warned by", value=member.mention)
		embed.add_field(name="Reason", value=reason)
		embed.timestamp = datetime.datetime.utcnow()

		report_message = await log_channel.send(embed=embed)
		query = "UPDATE event_logs SET report_message_id = $1 WHERE id = $2"
		await self.bot.pool.execute(query, report_message.id, log_id)

	@commands.command()
	@checks.is_mod()
	async def note(self, ctx, member: Member, reason):
		query = "INSERT into event_logs (action, target_id, user_id, guild_id, reason) VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "note", member.id, ctx.author.id, ctx.guild.id, reason)

		await ctx.message.add_reaction("\N{Thumbs Up Sign}")

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, member.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'User Noted - Mod Report #{log_id}')  # TODO Colour
		embed.add_field(name="User", value=member.mention)
		embed.add_field(name="Username", value=f'{member.name}#{member.discriminator}')
		embed.add_field(name="User ID", value=f'{member.id}')
		embed.add_field(name="Noted by", value=member.mention)
		embed.add_field(name="Reason", value=reason)
		embed.timestamp = datetime.datetime.utcnow()

		report_message = await log_channel.send(embed=embed)
		query = "UPDATE event_logs SET report_message_id = $1 WHERE id = $2"
		await self.bot.pool.execute(query, report_message.id, log_id)


	@commands.command()
	@checks.is_mod()
	async def update_log(self, ctx, log_number : int, *, reason):
		"""Update a log to include a new reason. N.B. This will also change the user who did this action to be you"""
		query = "SELECT * from event_logs WHERE id = $1"
		report = await self.bot.pool.fetchrow(query, log_number)

		if not report:
			return await ctx.send(embed=self.bot.error("This is not a valid report"))

		if report["guild_id"] != ctx.guild.id:
			return await ctx.send(embed=self.bot.error("This report does not belong to this guild"))

		query = "UPDATE event_logs SET user_id = $1, reason = $2 WHERE id = $3"
		await self.bot.pool.execute(query, ctx.author.id, reason, log_number)
		await ctx.message.add_reaction("\N{Thumbs Up Sign}")
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
			if field.name in ["Banned by", "Unbanned by", "Warned by", "Noted by", "Muted by"]:
				embed.set_field_at(counter, name=field.name, value=ctx.author.mention)
				field.value = ctx.author.mention
			if field.name == "Reason":
				embed.set_field_at(counter, name="Reason", value=reason)
		await log_report_message.edit(embed=embed)


	@commands.group(invoke_without_command=True)
	@commands.guild_only()
	@checks.is_admin()
	async def blacklist(self, ctx):
		"""ADVANCED: Group of commands for controlling blacklisted channel"""
		embed = Embed(title=f"Settings for {ctx.guild.name}")
		query = "SELECT whitelist, blacklist FROM log_config WHERE guild_id = $1"
		results = await self.bot.pool.fetchrow(query, ctx.guild.id)
		if results["whitelist"]:
			embed.description = "Guild currently setup as a whitelist. Only the listed channnels below will be recorded "
		else:
			embed.description = "Guild currently setup as a blacklist. Only the list channels below will not be recorded"
		channels = [self.bot.get_channel(channel_id) for channel_id in results["blacklist"]]
		channels = [channel.name for channel in channels if channel is not None]
		embed.add_field(name="Channels", value=("\n".join(channel.name for channel in channels) if channels else "No channels"))

	@blacklist.command()
	@commands.guild_only()
	@checks.is_admin()
	async def whitelist(self, ctx):
		"""Toggles between blacklist and whitelist"""
		updatequery = "UPDATE log_config SET whitelist = NOT whitelist WHERE guild_id = $1 RETURNING whitelist"
		insertquery = "INSERT into log_config (guild_id, whitelist) VALUES ($1, $2) RETURNING whitelist"
		try:
			whitelist = await self.bot.pool.fetchval(insertquery, ctx.guild.id, True)
		except asyncpg.UniqueViolationError:
			whitelist = await self.bot.pool.fetchval(updatequery, ctx.guild.id)

		if whitelist:
			await ctx.send(embed=self.bot.success("Whitelist is now on. Only messages in whitelisted channels will be recorded"))
		else:
			await ctx.send(emebd=self.bot.success("Whitelist not off. Only messages in blacklisted channels will be recorded"))

	@blacklist.command()
	@commands.guild_only()
	@checks.is_admin()
	async def add(self, ctx, channel: TextChannel):
		"""Adds a channel to the blacklist and delete the message history for this channel. If whitelist has been enabled this will add the channel to the whitelist instead"""
		query  = "SELECT * FROM log_config WHERE guild_id = $1"
		config = await self.bot.pool.fetchrow(query, ctx.guild.id)
		if not config:
			query = "INSERT INTO log_config (guild_id, blacklist) VALUES ($1, $2)"
			await self.bot.pool.execute(query, ctx.guild.id, [channel.id])
		else:
			blacklist = config["blacklist"]
			query = "UPDATE log_config SET blacklist = $1 WHERE guild_id = $2"
			await self.bot.pool.execute(query, (blacklist or []).extend([channel.id]))

		if not config["whitelist"]:
			query = "DELETE FROM message_logs WHERE channel_id = $1"
			await self.bot.pool.execute(query, channel.id)
			await ctx.send(embed=self.bot.success(f"{channel.mention} added to the blacklist and all message logs deleted"))
		else:
			await ctx.send(
				embed=self.bot.success(f"{channel.mention} added to the whitelist"))

	@blacklist.command()
	@commands.guild_only()
	@checks.is_admin()
	async def remove(self, ctx, channel: TextChannel):
		"""Removes a channel from the blacklist. If whitelist has been enabled this will remove the channel from the whitelist and delete the message logs instead"""
		query = "SELECT * FROM log_config WHERE guild_id = $1"
		config = await self.bot.pool.fetchrow(query, ctx.guild.id)
		if not config:
			await ctx.send(embed=self.bot.error("Channel not in the blacklist"))
			return

		channel_list = config["blacklist"] or []

		if channel.id in channel_list:
			channel_list = [channel for channel in channel_list if channel != channel.id]
			query = "UPDATE log_config SET blacklist = $1 WHERE guild_id = $2"
			await self.bot.pool.execute(query, channel_list, ctx.guild.id)
			if config["whitelist"]:
				query = "DELETE FROM message_logs WHERE channel_id = $1"
				await self.bot.pool.execute(query)
				await ctx.send(embed=self.bot.success(f"{channel.mention} removed from the whitelist and all message logs deleted"))
			else:
				await ctx.send(embed=self.bot.success(f"{channel.members} removed from the blacklist"))
		else:
			if config["whitelist"]:
				await ctx.send(self.bot.error(f"{channel.mention} not in the whitelist"))
			else:
				await ctx.send(self.bot.error(f"{channel.mention} not in the blacklist"))



	# Events

	async def on_guild_channel_delete(self, channel):  # Kind of like an auto firing command
		member_query = "UPDATE log_config SET member_log_channel_id = $1 WHERE member_log_channel_id = $2"
		message_query = "UPDATE log_config SET message_log_channel_id = $1 WHERE message_log_channel_id = $2"
		invite_query = "UPDATE log_config SET invite_log_channel_id = $1 WHERE invite_log_channel_id = $2"
		strike_query = "UPDATE log_config SET strike_log_channel_id = $1 WHERE strike_log_channel_id = $2"

		await self.bot.pool.execute(member_query, None, channel.id)
		await self.bot.pool.execute(message_query, None, channel.id)
		await self.bot.pool.execute(invite_query, None, channel.id)
		await self.bot.pool.execute(strike_query, None, channel.id)

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


	async def on_member_mute(self, member, reason, muter):
		query = "INSERT into event_logs (action, target_id, user_id, guild_id) VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "mute", member.id, None, member.guild.id)

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, member.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'User Muted - Mod Report #{log_id}', colour=0xFFA500)
		embed.add_field(name="User", value=member.mention)
		embed.add_field(name="Username", value=f'{member.name}#{member.discriminator}')
		embed.add_field(name="User ID", value=f'{member.id}')
		embed.add_field(name="Muted by", value=muter.mention)
		embed.add_field(name="Reason", value=reason)
		embed.timestamp = datetime.datetime.utcnow()
		report_message = await log_channel.send(embed=embed)
		query = "UPDATE event_logs SET user_id = $1, reason = $2, report_message_id = $3 WHERE id = $4"
		await self.bot.pool.execute(query, muter.id, reason, report_message.id, log_id)
		await report_message.add_reaction("🔊")

		async def check(reaction, user):
			if reaction.emoji != "🔊":
				return False

			if reaction.message is not report_message:
				return False
			return True

		reaction, user = await self.bot.wait_for("reaction_add", check=check)

		proxy_ctx = await self.bot.get_context(report_message)
		proxy_ctx.author = user
		await proxy_ctx.invoke(self.bot.get_command("unmuteall"), user=member)




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
		embed.add_field(name="Banned by", value=str(banner))
		embed.add_field(name="Reason", value=reason)

		embed.add_field(name="Message History",
		                value=f"[View Message History]({self.bot.root_website}/messages/{guild.id}/{user.id})\n[View Member Logs]({self.bot.root_website}/logs/{guild.id}/{user.id})",
		                inline=False)

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

		embed = Embed(title=f'Unbanned Banned - Mod Report #{log_id}')
		embed.add_field(name="User", value=user.mention)
		embed.add_field(name="Username", value =f'{user.name}#{user.discriminator}')
		embed.add_field(name="User ID", value=f'{user.id}')

		embed.timestamp = datetime.datetime.utcnow()
		query = "SELECT user_id, reason, time FROM event_logs WHERE (action = $1) and (target_id = $2) and (guild_id = $3) ORDER BY id DESC LIMIT 1"
		ban_info = await self.bot.pool.fetchrow(query, "ban", user.id, guild.id)
		if ban_info:
			banner = self.bot.get_user(ban_info["user_id"])
			reason = dict(ban_info).get("reason", "None Provided")
			embed.add_field(name="Originally banned by", value=banner.mention if banner else f"User with id: {ban_info['user_id']}")
			embed.add_field(name="Original ban reason", value=reason)
			embed.add_field(name="Originally banned", value=yoriutils.human_timedelta(ban_info["time"]))
		unbanner, unbanreason = await self.get_unban_info(guild, user)
		embed.add_field(name="Unbanned by", value=unbanner.mention)
		embed.add_field(name="Reason", value=unbanreason)

		report_message = await log_channel.send(embed=embed)
		query = "UPDATE event_logs SET user_id = $1, reason = $2, report_message_id = $3 WHERE id = $4"
		await self.bot.pool.execute(query, unbanner.id, unbanreason, report_message.id, log_id)

	async def on_member_strike(self, member, offence, reason):
		query = "INSERT into event_logs (action, target_id, user_id, guild_id, reason) VALUES ($1, $2, $3, $4, $5) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, offence, member.id, self.bot.user.id, member.guild.id, reason)

		query = "SELECT strike_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, member.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'User Strike', colour=0xFFA500)
		embed.add_field(name="User", value=member.mention)
		embed.add_field(name="Username", value=f'{member.name}#{member.discriminator}')
		embed.add_field(name="User ID", value=f'{member.id}')
		embed.timestamp = datetime.datetime.utcnow()
		embed.add_field(name="Triggered Automod", value=offence, inline=False)
		embed.add_field(name="Offending message", value=reason)
		await log_channel.send(embed=embed)

	async def on_message(self, message):
		if message.author is self.bot.user:
			return
		if message.channel.id in self.black_listed_channels:
			return
		query = "INSERT INTO message_logs (message_id, content, author_id, channel_id, guild_id, status) VALUES ($1, $2, $3, $4, $5, $6)"
		await self.bot.pool.execute(query, message.id, message.content, message.author.id, message.channel.id, message.guild.id, "current")

	async def on_message_delete(self, message):
		if message.author is self.bot.user:
			return
		if message.channel.id in self.black_listed_channels:
			return
		query = "UPDATE message_logs SET status = $1 WHERE message_id = $2"
		await self.bot.pool.execute(query, "deleted", message.id)

		query = "SELECT message_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, message.channel.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'Message Removed')
		embed.add_field(name="User", value=message.author.mention)
		embed.add_field(name="User Name", value=f'{message.author.name}{message.author.discriminator}')
		embed.add_field(name="User ID", value=f'{message.author.id}')
		embed.add_field(name="Channel", value=f'{message.channel.mention}')
		embed.add_field(name="Channel ID", value=f'{message.channel.id}')
		embed.add_field(name="Message Content", value=message.content if message.content else "*empty*", inline=False)
		embed.timestamp = datetime.datetime.utcnow()

		await log_channel.send(embed=embed)

	async def on_message_edit(self, before, after):
		if before.author.bot:
			return
		if after.channel.id in self.black_listed_channels:
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
					new_invites = await self.gather_new_invites(guild)
					if new_invites:
						self.invites[guild] = new_invites
				except Forbidden:
					pass
			await asyncio.sleep(60)

	async def gather_new_invites(self, guild):
		new_invites = await guild.invites()
		old_invites = self.invites.get(guild)
		if old_invites:
			query = "SELECT invite_log_channel_id FROM log_config WHERE guild_id = $1"
			log_channel_id = await self.bot.pool.fetchval(query, guild.id)
			log_channel = self.bot.get_channel(log_channel_id)
			if log_channel:
				created_invites = list(set(new_invites) - set(old_invites))
				expired_invites = list(set(old_invites) - set(new_invites))
				for invite in created_invites:
					embed = Embed(title=f'Invited Created')
					embed.add_field(name="Invite Code", value=invite.code)
					embed.add_field(name="Created by", value=invite.inviter or "Widget")
					embed.timestamp = datetime.datetime.utcnow()
					await log_channel.send(embed=embed)
				for invite in expired_invites:
					embed = Embed(title=f'Invited expired')
					embed.add_field(name="Invite Code", value=invite.code)
					embed.add_field(name="Created by", value=invite.inviter or "Widget")
					embed.add_field(name="Used", value=f'{invite.uses} times')
					embed.timestamp = datetime.datetime.utcnow()
					await log_channel.send(embed=embed)
		return new_invites

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
					reasonunbanned = "No Reason Provided"
			return unbanner, reasonunbanned
		except Forbidden:
			return "No access to Audit Logs", "No access to Audit Logs"

	async def update_blacklist_cache(self):
		query = "SELECT blacklist FROM log_config"
		results = await self.bot.fetch(query)
		for guild in results:
			if guild["blacklist"]:
				self.black_listed_channels += guild["blacklist"]





def setup(bot):
	bot.add_cog(Logs(bot))
