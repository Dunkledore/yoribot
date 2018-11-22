from discord import Member, TextChannel
from discord.ext import commands

from .utils import checks
from .utils.utils import check_hierarchy


class Moderation:
	"""Commands related to moderating users"""

	def __init__(self, bot):
		self.bot = bot
		self.category = "Admin and Moderation"

	# Commands #

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def ban(self, ctx, user: Member, *, reason=None):
		"""Ban a member from the guild"""
		if not check_hierarchy(ctx.author, user):
			return await ctx.send(embed=self.bot.error("You can't ban someone with a higher rank than you"))
		if not reason:
			reason = f"Banned by {ctx.author.name}"

		await user.ban(reason=reason, delete_message_days=7)
		await ctx.send(embed=self.bot.success(f'Member {user.name} banned'))

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def unban(self, ctx, user: str, *, reason=None):
		"""Unban a member from the guild"""
		bans = await ctx.guild.bans()
		if user.isdigit():  # This part checks to see if the user is banned and avoids us having to create a proxy member
			user_objs = [banned_user.user for banned_user in bans if banned_user.user.id == user.id]
		else:
			user_objs = [banned_user.user for banned_user in bans if banned_user.user.name == user]
		if user_objs:
			if not reason:
				reason = f"Unbanned by {ctx.author.name}"
			await ctx.guild.unban(user_objs[0], reason=reason)
			await ctx.send(embed=self.bot.success(f"Member {user_obj.name} unbanned"))
		else:
			await ctx.send(embed=self.bot.error("This is not a banned user"))

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def tempban(self, ctx, user: Member, reason=None):  # TODO
		"""Temporarily ban a member from the guild"""
		pass

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def softban(self, ctx, user: Member, reason):  # TODO
		"""A ban a then an immediate unbam. The same as a kick but also deletes messages"""
		pass

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def kick(self, ctx, user: Member, *, reason=None):
		"""Kicks a member from the guild"""
		if not check_hierarchy(ctx.author, user):
			return await ctx.send(embed=self.bot.error("You can't kick someone with a higher rank than you"))
		if not reason:
			reason = f"Kicked by {ctx.author.name}"
		await user.kick(reason=reason)
		await ctx.send(embed=self.bot.success(f'Member {user.name} kicked'))

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def mute(self, ctx, user: Member, channel: TextChannel = None, *, reason=None):
		"""Mutes a user in the specified channel, if not specified, in the channel the command is used from."""
		if not check_hierarchy(ctx.author, user):
			return await ctx.send(embed=self.bot.error("You can't mute someone with a higher rank than you"))
		if channel is None:
			channel = ctx.channel
		await channel.set_permissions(user, reason=reason, send_messages=False)
		await ctx.send(embed=self.bot.success(f'Member {user.name} muted in this channel'))
		self.bot.dispatch("member_mute", user, reason, ctx.author)

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def unmute(self, ctx, user: Member, channel: TextChannel = None, *, reason=None):
		"""Unmutes a user in the specified channel, if not specified, in the channel the command is used from."""
		if channel is None:
			channel = ctx.channel
		await channel.set_permissions(user, reason=reason or f"Unmute by {ctx.author}", send_messages=None)
		await ctx.send(embed=self.bot.success(f'Member {user.name} Unmuted in this channel'))

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def muteall(self, ctx, user: Member, reason=None):
		"""Mutes a user in all channels of this server."""
		if not check_hierarchy(ctx.author, user):
			return await ctx.send(embed=self.bot.error("You can't kick someone with a higher rank than you"))
		for tchan in ctx.guild.text_channels:
			await tchan.set_permissions(user, reason=f"Mute in all channels by {ctx.author}", send_messages=False)
		await ctx.send(embed=self.bot.success(f'Member {user.name} muted in this guild'))
		self.bot.dispatch("member_mute", user, reason, ctx.author)

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def unmuteall(self, ctx, user: Member):
		"""Unmutes a user in all channels of this server."""
		for tchan in ctx.guild.text_channels:
			if tchan.overwrites_for(user) and not tchan.overwrites_for(user).is_empty():
				await tchan.set_permissions(user, reason=f"Unmute in all channels by {ctx.author}", send_messages=None)
		await ctx.send(embed=self.bot.success(f'Member {user.name} unmuted in this guild'))


def setup(bot):
	bot.add_cog(Moderation(bot))
