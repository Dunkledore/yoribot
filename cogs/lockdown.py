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

	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def lockdown(self, ctx):
		"Toggles the lockdown mode"
		guild = ctx.message.guild
		mod_role_id = self.get_mod_role_id(guild)
		role_list = [role for role in guild.roles if role.id != mod_role_id]
		if str(guild.id) in self.settings:
			for channel in guild.channels:
				if str(channel.id) in self.settings[str(guild.id)]["channels"] and self.settings[str(guild.id)]["channels"][str(channel.id)]:
					for role in role_list:
						cur_role_perms = channel.overwrites_for(role)
						cur_role_perms.send_messages = False
						print("Editing channel permissions for {}".format(role.name))
						await channel.set_permissions(role, cur_role_perms)
					bot_perms = channel.overwrites_for(guild.me)
					bot_perms_edited = False
					if not bot_perms.read_messages:
						bot_perms.read_messages = True
						bot_perms_edited = True
					if not bot_perms.send_messages:
						bot_perms.send_messages = True
						bot_perms_edited = True
					if bot_perms_edited:
						await channel.set_permissions(guild.me, bot_perms)
			await ctx.send("guild is locked down. You can unlock the guild by doing {}unlockdown".format(ctx.prefix))
		else:
			await ctx.send("No settings available for this guild!")

	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def unlockdown(self, ctx):
		"""Ends the lockdown for this guild"""
		guild = ctx.message.guild
		mod_role_id = self.get_mod_role_id(guild)
		admin = self.bot.settings.get_guild_admin(guild)
		role_list = [role for role in guild.roles if role.id != mod_role_id]
		if str(guild.id) in self.settings:
			for channel in guild.channels:
				if str(channel.id) in self.settings[str(guild.id)]["channels"] and self.settings[str(guild.id)]["channels"][str(channel.id)]:
					for role in role_list:
						cur_role_perms = channel.overwrites_for(role)
						cur_role_perms.send_messages = None
						print("Editing channel permissions for {}".format(role.name))
						await channel.set_permissions(ole, cur_role_perms)
			await ctx.send("guild has been unlocked!")
		else:
			await ctx.send("No settings available for this guild!")

	@commands.command()
	@commands.guild_only()
	async def lockchanset(self, ctx, channel: discord.TextChannel, status: str):
		"""Sets whether or not the channel will be
		   locked down if a lockdown is turned on
		   Options for status are on or off"""
		guild = ctx.message.guild
		new_status = None
		if status.lower() not in ["on", "off"]
			ctx.send("Invalid status specified!")
			return
		else:
			new_status = (status.lower() == "on")
		if str(guild.id) not in self.settings:
			self.settings[guild.id] = {}
		if "channels" not in self.settings[str(guild.id)]:
			self.settings[guild.id]["channels"] = {}
		if str(channel.id) not in self.settings[str(guild.id)]["channels"]:
			self.settings[str(guild.id)]["channels"][str(channel.id)] = None
		self.settings[str(guild.id)]["channels"][str(channel.id)] = new_status
		dataIO.save_json("data/lockdown/settings.json", self.settings)
		await ctx.send("New status for {} set!".format(channel.mention))

	async def get_mod_role_id(self, guild):
		query = "SELECT * FROM mod_config WHERE guild_id = $1"
		results = await self.bot.pool.fetchrow(query, guild.id)

		if results:
			return results["mod_role"]


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