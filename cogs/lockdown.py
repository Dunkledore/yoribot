from discord.ext import commands
import discord
import os
from .utils import checks
from .utils.dataIO import dataIO


class Lockdown():
	"""Locks down the current guild"""

	def __init__(self, bot):
		self.bot = bot
		self.settings = dataIO.load_json("data/lockdown/settings.json")

	@commands.command(pass_context=True, no_pm=True)
	@checks.is_mod()
	async def lockdown(self, ctx):
		"Toggles the lockdown mode"
		guild = ctx.message.guild
		mod = self.bot.settings.get_guild_mod(guild)
		admin = self.bot.settings.get_guild_admin(guild)
		role_list = [role for role in guild.roles if role.name != mod and role.name != admin]
		if guild.id in self.settings:
			for channel in guild.channels:
				if channel.id in self.settings[guild.id]["channels"] and\
						self.settings[guild.id]["channels"][channel.id]:
					for role in role_list:
						cur_role_perms = channel.overwrites_for(role)
						cur_role_perms.send_messages = False
						print("Editing channel permissions for {}".format(role.name))
						await self.bot.edit_channel_permissions(channel, role, cur_role_perms)
					bot_perms = channel.overwrites_for(guild.me)
					bot_perms_edited = False
					if not bot_perms.read_messages:
						bot_perms.read_messages = True
						bot_perms_edited = True
					if not bot_perms.send_messages:
						bot_perms.send_messages = True
						bot_perms_edited = True
					if bot_perms_edited:
						await self.bot.edit_channel_permissions(channel, guild.me, bot_perms)
			ctx.send(
				"guild is locked down. You can unlock the guild by doing {}unlockdown".format(
					ctx.prefix
				)
			)
		else:
			ctx.send("No settings available for this guild!")

	@commands.command(pass_context=True, no_pm=True)
	@checks.is_mod()
	async def unlockdown(self, ctx):
		"""Ends the lockdown for this guild"""
		guild = ctx.message.guild
		mod = self.bot.settings.get_guild_mod(guild)
		admin = self.bot.settings.get_guild_admin(guild)
		role_list = [role for role in guild.roles if role.name != mod and role.name != admin]
		if guild.id in self.settings:
			for channel in guild.channels:
				if channel.id in self.settings[guild.id]["channels"] and\
						self.settings[guild.id]["channels"][channel.id]:
					for role in role_list:
						cur_role_perms = channel.overwrites_for(role)
						cur_role_perms.send_messages = None
						print("Editing channel permissions for {}".format(role.name))
						await self.bot.edit_channel_permissions(channel, role, cur_role_perms)
			ctx.send("guild has been unlocked!")
		else:
			ctx.send("No settings available for this guild!")

	@commands.command(pass_context=True, no_pm=True)
	async def lockchanset(self, ctx, channel: discord.Channel, status: str):
		"""Sets whether or not the channel will be
		   locked down if a lockdown is turned on
		   Options for status are on or off"""
		guild = ctx.message.guild
		new_status = None
		if status.lower() != "on" and status.lower() != "off":
			ctx.send("Invalid status specified!")
			return
		else:
			if status.lower() == "on":
				new_status = True
			else:
				new_status = False
		if guild.id not in self.settings:
			self.settings[guild.id] = {}
		if "channels" not in self.settings[guild.id]:
			self.settings[guild.id]["channels"] = {}
		if channel.id not in self.settings[guild.id]["channels"]:
			self.settings[guild.id]["channels"][channel.id] = None
		self.settings[guild.id]["channels"][channel.id] = new_status
		dataIO.save_json("data/lockdown/settings.json", self.settings)
		ctx.send("New status for {} set!".format(channel.mention))


def check_folder():
	if not os.path.isdir("data/lockdown"):
		os.mkdir("data/lockdown")


def check_file():
	if not dataIO.is_valid_json("data/lockdown/settings.json"):
		dataIO.save_json("data/lockdown/settings.json", {})


def setup(bot):
	check_folder()
	check_file()
	bot.add_cog(Lockdown(bot))