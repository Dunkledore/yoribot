from copy import deepcopy
import os

import discord
import datetime
from discord.ext import commands

from .utils.dataIO import dataIO
from .utils import checks, time, chat_formatting as cf


default_settings = {
	"join_message": "{0.mention} has joined the server.",
	"leave_message": "{0.display_name} has left the server.",
	"ban_message": "{0.display_name} has been banned.",
	"unban_message": "{0.display_name} has been unbanned.",
	"on": False,
	"channel": None,
	"raid": False,
	"auto_raid" : False
}


class MemberAudit:

	"""Sets up a channel where you can receive notifications of when people join, leave, are banned or unbanned."""

	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.settings_path = "data/membership/settings.json"
		self.settings = dataIO.load_json(self.settings_path)


	def checksettings(self, ctx):
		server = ctx.message.guild
		if str(server.id) not in self.settings:
			self.settings[str(server.id)] = deepcopy(default_settings)
			self.settings[str(server.id)]["channel"] = str(server.text_channels[0].id)
			dataIO.save_json(self.settings_path, self.settings)

	@commands.command(no_pm=True)
	@checks.is_admin()
	async def auto_raid(self, ctx):
		"""Toggles Auto-Raid
		Auto-Raid On: Will turn raid on if 3 people join within 1 minute
		Auto_Raid Off: Raid mode will never be automatically turned on"""

		self.settings[str(ctx.guild.id)]["raid"] = not self.settings[str(ctx.guild.id)]["raid"]

		if self.settings[str(ctx.guild.id)]["raid"]:
			await ctx.send("Auto-Raid On")
		else:
			await ctx.send("Auto-Raid Off")

		dataIO.save_json(self.settings_path, self.settings)


	@commands.command(no_pm=True)
	@checks.is_admin()
	async def temp_raid(self, ctx):
		await self._raid(ctx)#temp to enable raid

	async def _raid(self, ctx): #Seperate definition to allow other definitions to call raid. 
		"""Toggles Raid Mode
		Raid On: Moderation Level will be set to High. Users must be in for more than 10 minutes before speaking
		Raid Off: Morderation Level will be set to Low. Users must have a email on their discord account befores speaking"""

		self.settings[str(ctx.guild.id)]["raid"] = not self.settings[str(ctx.guild.id)]["raid"]

		if  self.settings[str(ctx.guild.id)]["raid"]:
			try:
				await ctx.guild.edit(verification_level=discord.VerificationLevel.high)
				await ctx.send('Raid On')
			except discord.HTTPException:
				await ctx.send('\N{WARNING SIGN} Could not set verification level.')
		else:
			try:
				await ctx.guild.edit(verification_level=discord.VerificationLevel.low)
				await ctx.send('Raid Off')
			except discord.HTTPException:
				await ctx.send('\N{WARNING SIGN} Could not set verification level.')
		
		dataIO.save_json(self.settings_path, self.settings)


	@commands.command(no_pm=True)
	@checks.is_mod()
	async def log(self, ctx, member : discord.Member,*,  reason=None):
		"""Add an entry to a mod log about a member"""

		if reason:
			query = "INSERT INTO mod_log (guild_id, user_id, user_name, action, reason, mod_id, mod_name) VALUES ($1, $2, $3, $4, $5, $6, $7)"
			await ctx.db.execute(query, ctx.guild.id, member.id, member.nick or member.name, 'Note', reason, ctx.author.id, ctx.author.name)
		
		embed = await self.log_as_embed(member.id, ctx.guild.id)
		await ctx.send(embed=embed)

	@commands.command(no_pm=True)
	@checks.is_mod()
	async def modlog(self, ctx, member):
		converter = commands.MemberConverter()
		converted = None
		
		converted = await converter.convert(ctx, member)


		if converted:
			embed = await self.log_as_embed(converted.id, ctx.guild.id)
		else:
			embed = await self.log_as_embed(member, ctx.guild.id)

		if embed:
			await ctx.send(embed=embed)
		else:
			await ctx.send("No mod logs found")

	@commands.command(no_pm=True)
	@checks.is_admin()
	async def joinaudit(self, ctx: commands.Context, *,
					format_str: str):
		"""Sets the join/greeting/welcome message for the server.
		{0} is the member
		{1} is the server
		"""
		self.checksettings(ctx)
		server = ctx.message.guild
		self.settings[str(server.id)]["join_message"] = format_str
		dataIO.save_json(self.settings_path, self.settings)
		await ctx.send(cf.info("Join message set."))

	@commands.command(no_pm=True)
	@checks.is_admin()
	async def leaveaudit(self, ctx: commands.Context, *,
					 format_str: str):
		"""Sets the leave/farewell message for the server.
		{0} is the member
		{1} is the server
		"""
		self.checksettings(ctx)
		server = ctx.message.guild
		self.settings[str(server.id)]["leave_message"] = format_str
		dataIO.save_json(self.settings_path, self.settings)
		await ctx.send(cf.info("Leave message set."))

	@commands.command(no_pm=True)
	@checks.is_admin()
	async def banaudit(self, ctx: commands.Context, *, format_str: str):
		"""Sets the ban message for the server.
		{0} is the member
		{1} is the server
		"""
		self.checksettings(ctx)
		server = ctx.message.guild
		self.settings[str(server.id)]["ban_message"] = format_str
		dataIO.save_json(self.settings_path, self.settings)
		await ctx.send(cf.info("Ban message set."))

	@commands.command(no_pm=True)
	@checks.is_admin()
	async def unbanaudit(self, ctx: commands.Context, *, format_str: str):
		"""Sets the unban message for the server.
		{0} is the member
		{1} is the server
		"""
		self.checksettings(ctx)
		server = ctx.message.guild
		self.settings[str(server.id)]["unban_message"] = format_str
		dataIO.save_json(self.settings_path, self.settings)
		await ctx.send(cf.info("Unban message set."))

	@commands.command(no_pm=True)
	@checks.is_admin()
	async def audittoggle(self, ctx: commands.Context):
		"""Turns membership event commands on or off."""

		self.checksettings(ctx)
		server = ctx.message.guild
		self.settings[str(server.id)]["on"] = not self.settings[str(server.id)]["on"]
		if self.settings[str(server.id)]["on"]:
			await ctx.send(
				cf.info("Membership events will now be announced."))
		else:
			await ctx.send(
				cf.info("Membership events will no longer be announced."))
		dataIO.save_json(self.settings_path, self.settings)

	@commands.command(no_pm=True)
	@checks.is_admin()
	async def auditchannel(self, ctx: commands.Context,
					   channel: discord.TextChannel=None):
		"""Sets the text channel to which the announcements will be sent.

		 If none is specified, the default will be used.
		 """
		
		self.checksettings(ctx)
		await ctx.send('Command Invoked')
		server = ctx.message.guild

		if not channel:
			channel = server.text_channels[0]

		if not self.speak_permissions(server, channel):
			await ctx.send(
				"I don't have permission to send messages in {0.mention}."
				.format(channel))
			return

		self.settings[str(server.id)]["channel"] = channel.id
		dataIO.save_json(self.settings_path, self.settings)
		channel = self.get_welcome_channel(server)
		await channel.send(  ("{0.mention}, " +
									 cf.info(
										 "I will now send membership"
										 " announcements to {1.mention}."))
									.format(ctx.message.author, channel))

	async def member_join(self, member: discord.Member):
		server = member.guild
		if str(server.id) not in self.settings:
			self.settings[str(server.id)] = deepcopy(default_settings)
			self.settings[str(server.id)]["channel"] = str(server.text_channels[0].id)
			dataIO.save_json(self.settings_path, self.settings)

		ch = self.get_welcome_channel(server)

		if not self.settings[str(server.id)]["on"] or ch is None:
			return
		
		await ch.trigger_typing()

		if server is None:
			print("The server was None, so this was either a PM or an error."
				  " The user was {}.".format(
					  member.name))
			return 
		bannedin= ""
		for guild in self.bot.guilds:
			bans = await guild.bans()
			for banentry in bans:
				if member == banentry[1]:
					bannedin += guild.name + '\n'

		created = (datetime.datetime.utcnow() - member.created_at).total_seconds() // 60
		if created < 30 or bannedin:
			colour = 0xdda453
		else:
			colour = 0x53dda4

		channel = self.get_welcome_channel(server)
		if self.speak_permissions(server, channel):
			embed = discord.Embed(title = "📥 Member Join", description = self.settings[str(server.id)]["join_message"].format(member, server), colour = colour)
			embed.timestamp = datetime.datetime.utcnow()
			embed.set_footer(text='Joined')
			embed.set_author(name=str(member), icon_url=member.avatar_url)
			embed.add_field(name='ID', value=member.id)
			embed.add_field(name='Joined', value=member.joined_at)
			embed.add_field(name='Created', value=time.human_timedelta(member.created_at), inline=False)
			if bannedin:
				embed.add_field(name='Banned In', value = bannedin)

			await channel.send(embed=embed)
		else:
			print("Tried to send message to channel, but didn't have"
				  " permission. User was {}.".format(member))

	async def member_leave(self, member: discord.Member):
		server = member.guild
		if str(server.id) not in self.settings:
			self.settings[str(server.id)] = deepcopy(default_settings)
			self.settings[str(server.id)]["channel"] = str(server.text_channels[0].id)
			dataIO.save_json(self.settings_path, self.settings)

		ch = self.get_welcome_channel(server)

		if not self.settings[str(server.id)]["on"] or ch is None:
			return
		
		await ch.trigger_typing()

		if server is None:
			print("The server was None, so this was either a PM or an error."
				  " The user was {}.".format(member.name))
			return

		channel = self.get_welcome_channel(server)
		if self.speak_permissions(server, channel):
			await channel.send(embed=discord.Embed(
								title = "📤 Member Leave",
								description = self.settings[str(server.id)]["leave_message"].format(member, server)
								))

		else:
			print("Tried to send message to channel, but didn't have"
				  " permission. User was {}.".format(member))

	async def member_ban(self, guild, user: discord.User):
		server = guild
		if str(server.id) not in self.settings:
			self.settings[server.id] = deepcopy(default_settings)
			self.settings[server.id]["channel"] = str(server.text_channels[0].id)
			dataIO.save_json(self.settings_path, self.settings)
		
		ch = self.get_welcome_channel(server)

		if not self.settings[str(server.id)]["on"] or ch is None:
			return
		
		await ch.trigger_typing()

		if server is None:
			print("The server was None, so this was either a PM or an error."
				  " The user was {}.".format(user.name))
			return

		channel = self.get_welcome_channel(server)
		if self.speak_permissions(server, channel):
			await channel.send(embed=discord.Embed(
								title = "🔨 Member Banned",
								description = self.settings[str(server.id)]["ban_message"].format(user, server)
								))
		else:
			print("Tried to send message to channel, but didn't have"
				  " permission. User was {}.".format(user.name))

	async def member_unban(self, guild, user: discord.User):
		server = guild
		if str(server.id) not in self.settings:
			self.settings[str(server.id)] = deepcopy(default_settings)
			self.settings[str(server.id)]["channel"] =  str(server.text_channels[0].id)
			dataIO.save_json(self.settings_path, self.settings)

		ch = self.get_welcome_channel(server)

		if not self.settings[str(server.id)]["on"] or ch is None:
			return
		
		await ch.trigger_typing()

		if server is None:
			print("The server was None, so this was either a PM or an error."
				  " The user was {}.".format(
					  user.name))
			return

		channel = self.get_welcome_channel(server)
		if self.speak_permissions(server, channel):
			await channel.send(embed=discord.Embed(
								title = "🕊️ Member Leave",
								description = self.settings[str(server.id)]["unban_message"].format(user, server)
								))
		else:
			print("Tried to send message to channel, but didn't have"
				  " permission. User was {}.".format(user.name))

	async def log_as_embed(self, user_id, guild_id):
		query = "SELECT * FROM mod_log WHERE user_id = $1 AND guild_id = $2"
		pool = self.bot.pool
		results = await pool.fetch(query, user_id, guild_id)
		
		embed = discord.Embed(title = 'Mod Log for: ' + str(user_id))
		
		member = self.bot.get_user(user_id)

		aliases = ""
		aliases += member.name + '\n'
		for result in results:
			if result['user_name']:
				if result['user_name'] not in aliases:
					aliases += result['user_name'] + '\n'
		if not aliases:
			return None
		actions = ""
		for result in results:
			actions += result['action']
			if result['reason']:
				actions += ' - ' + result['reason']
			if result['mod_name']:
				actions += '- By ' + result['mod_name']
			if actions:
				actions += '\n'

		embed.add_field(name='Aliases', value=aliases, inline=False)

		if actions:
			embed.add_field(name='Actions', value=actions, inline=False)

		if member:
			embed.add_field(name='Created', value=time.human_timedelta(member.created_at), inline=False)

		return embed







	def get_welcome_channel(self, guild: discord.Guild):
		return guild.get_channel(int(self.settings[str(guild.id)]["channel"]))

	async def get_mod_channel(self, guild :discord.Guild):
		query = "SELECT * FROM mod_config WHERE guild_id = $1"
		results = await self.bot.pool.fetch(query, guild.id)
		if results:
			mod_channel_id = results[0]["mod_channel"]
			return guild.get_channel(mod_channel_id)
		return None



	def speak_permissions(self, server: discord.Guild,
						  channel: discord.TextChannel=None):
		if not channel:
			channel = self.get_welcome_channel(server)
		member  =  server.get_member(self.bot.user.id)
		return member.permissions_in(channel).send_messages

		
def check_folders():
	if not os.path.exists("data/membership"):
		print("Creating data/membership directory...")
		os.makedirs("data/membership")


def check_files():
	f = "data/membership/settings.json"
	if not dataIO.is_valid_json(f):
		print("Creating data/membership/settings.json...")
		dataIO.save_json(f, {})


def setup(bot: commands.Bot):
	check_folders()
	check_files()
	n = MemberAudit(bot)
	bot.add_listener(n.member_join, "on_member_join")
	bot.add_listener(n.member_leave, "on_member_remove")
	bot.add_listener(n.member_ban, "on_member_ban")
	bot.add_listener(n.member_unban, "on_member_unban")
	bot.add_cog(n)
