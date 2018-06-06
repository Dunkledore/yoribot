from discord.ext import commands
from .utils import checks, utils
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
			await self.bot.pool.execute(alterquery, ctx.guild.id, channel.id)

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

	# Events

	async def on_guild_channel_delete(self, channel):  # Kind of like and auto firing commands
		member_query = "UPDATE log_config SET member_log_channel_id = $1 WHERE member_log_channel_id = $2"
		message_query = "UPDATE log_config SET message_log_channel_id = $1 WHERE message_log_channel_id = $2"
		invite_query = "UPDATE log_config SET invite_log_channel_id = $1 WHERE invite_log_channel_id = $2"

		await self.bot.pool.execute(member_query, None, channel.id)
		await self.bot.pool.execute(message_query, None, channel.id)
		await self.bot.pool.execute(invite_query, None, channel.id)

	async def on_member_join(self, member):

		query = "INSERT into event_logs (action, target_id, user_id, guild_id VALUES ($1, $2, $3, $4) RETURNING ID"
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

		embed = Embed(title=f'User Joined - Mod Report #{log_id}', colour=colour)  # TODO Colour
		embed.add_field(name="Username", value=f'{member.name}{member.discriminator} - {member.mention}')
		embed.add_field(name="User ID", value=f'{member.id}')
		embed.add_field(name='Created', value=utils.human_timedelta(member.created_at))
		embed.timestamp = datetime.datetime.utcnow()

		invites = await self.get_most_recent_used_invites_for_guild(member.guild)
		if not invites:
			invite = "Unknown"
		else:
			invite = "\n".join(invites)
		embed.add_field(name='Invite', value=invite)

		bans = await self.get_yori_bans(member)
		if bans:
			embed.colour = 0xdda453
			embed.add_field(name="Servers Banned In:", value="\n".join([guild.name for guild in bans]), inline=False)

		query = "SELECT guild_id FROM log_config WHERE mod_participation = $1"
		participating_guilds = await self.bot.pool.fetch(query, True)
		participating_guilds = [participating_guild["guild_id"] for participating_guild in participating_guilds]
		query = f'SELECT DISTINCT guild_id FROM event_logs WHERE (target_id = $1) and (guild_id in {tuple(participating_guilds)})'
		guilds_id_with_logs = await self.bot.pool.fetch(query, member.id)
		guilds_with_logs = []
		for guild_id in guilds_id_with_logs:
			guild = self.bot.get_guild(guild_id)
			guilds_with_logs.append(guild)

		if guilds_with_logs:
			embed.add_field(name="Mod Logs", value="\n".join(
				[f'[{guild.name}]({self.bot.root_website}/logs/{guild.id}/{member.id}' for guild in guilds_with_logs]))

		await log_channel.send(embed=embed)

	async def on_member_remove(self, member):

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, member.guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(color=0xFFA500, title="📤 Member Left")
		embed.timestamp = datetime.datetime.utcnow()
		embed.set_footer(text='Left')
		embed.set_author(name=str(member), icon_url=member.avatar_url)
		embed.add_field(name='ID', value=member.id)
		embed.add_field(name='Member', value=member.mention)
		embed.set_thumbnail(url=member.avatar_url)
		await log_channel.send(embed=embed)

	async def on_member_ban(self, guild, user):

		query = "INSERT into event_logs (action, target_id, user_id, guild_id VALUES ($1, $2, $3, $4) RETURNING ID"
		log_id = await self.bot.pool.fetchval(query, "join", user.id, None, guild.id)

		query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query, guild.id)
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title=f'User Joined - Mod Report #{log_id}', color=0xdf2a2a)
		embed.add_field(name="Username", value=f'{user.name}{user.discriminator} - {user.mention}')
		embed.add_field(name="User ID", value=f'{user.id}')
		embed.timestamp = datetime.datetime.utcnow()
		banner, reason = await self.get_ban_info(guild, user)
		embed.add_field(name="Banned by", value=banner)
		embed.add_field(name="Reason", value=reason)

		embed.add_field(name="Message History",
		                value=f"[View Message History]({self.bot.root_website}/messages/{guild.id}/{member.id})")

	async def on_member_unban(self, guild, user):
		pass

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
				current_invites = await guild.invite()
				for new_invite in current_invites:
					previous_invite = utils.get(previous_invites, code=new_invite.code)
					if previous_invite:
						if previous_invite.uses < new_invite.uses:
							most_recent_used_invites.append(f'{new_invite.code} - {new_invite.inviter or "Widget"}')
					elif new_invite.uses > 0:
						most_recent_used_invites.append(f'{new_invite.code} - {new_invite.inviter or "Widget"}')

			return most_recent_used_invites
		except Forbidden:
			return ["Unknown - Please enable the Manage Guild Permission"]

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
			return banner.mention, reasonbanned
		except Forbidden:
			return "No access to Audit Logs", "No access to Audit Logs"


def setup(bot):
	bot.add_cog(Logs(bot))
