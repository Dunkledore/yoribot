from .utils import checks
from .utils.utils import check_hierarchy
from discord.ext import commands
from discord import Member, utils, TextChannel
from datetime import datetime, timedelta

class Moderation:

	def __init__(self, bot):
		self.bot = bot

	# Commands #

	@commands.command()
	@checks.is_mod()
	async def ban(self, ctx, user : Member, reason=None):
		if not check_hierarchy(ctx.author, user):
			return await ctx.send(embed=self.bot.error("You can't ban someone with a higher rank than you"))
		if not reason:
			reason = f"Banned by {ctx.author.name}"

		await user.ban(reason=reason, delete_message_days=7)
		await ctx.send(embed=self.bot.success(f'Member {user.name} banned'))

	@commands.command()
	@checks.is_mod()
	async def unban(self, ctx, user: str, reason=None):
		bans = await ctx.guild.bans()
		if user.isdigit(): # This part checks to see if the user is banned and avoids us having to create a proxy member
			user = [banned_user[0] for banned_user in bans if banned_user[0].id == user][0]
		else:
			user = [banned_user[0] for banned_user in bans if banned_user[0].name == user][0]
			if not user:
				user = [banned_user[0] for banned_user in bans if str(banned_user[0]) == user][0]
		if user:
			if not reason:
				reason = f"Unbanned by {ctx.author.name}"
			await user.unban(reason=reason)
			await ctx.send(embed=self.bot.success(f"Member {user.name} unbanned"))
		else:
			await ctx.send(embed=self.bot.error("This is not a banned user"))


	@commands.command()
	@checks.is_mod()
	async def tempban(self, ctx, user : Member, reason=None):  # TODO
		pass


	@commands.command()
	@checks.is_mod()
	async def softban(self, ctx, user : Member, reason):  # TODO
		pass


	@commands.command()
	@checks.is_mod()
	async def kick(self, ctx, user : Member, reason):
		if not check_hierarchy(ctx.author, user):
			return await ctx.send(embed=self.bot.error("You can't kick someone with a higher rank than you"))
		if not reason:
			reason = f"Kicked by {ctx.author.name}"

		await user.kick(reason=reason, delete_message_days=7)
		await ctx.send(embed=self.bot.success(f'Member {user.name} kicked'))

	@commands.command()
	@commands.guild_only()
	@checks.is_mod()
	async def mute(self, ctx, user: Member, channel: TextChannel = None, reason = None):
		"""Mutes a user in the specified channel, if not specified, in the channel the command is used from."""
		if channel is None:
			channel = ctx.channel
		await channel.set_permissions(user, reason=reason or f"Mute by {ctx.author}", send_messages=False)
		await ctx.send(embed=self.bot.success(f'Member {user.name} muted in this channel'))

	@commands.command()
	@checks.is_mod()
	async def unmute(self, ctx, user : Member, reason):
		async def mute(self, ctx, user: Member, channel: TextChannel = None, reason=None):
			"""Unmutes a user in the specified channel, if not specified, in the channel the command is used from."""
			if channel is None:
				channel = ctx.channel
			await channel.set_permissions(user, reason=reason or f"Unmute by {ctx.author}", send_messages=None)
			await ctx.send(embed=self.bot.success(f'Member {user.name} Unmuted in this channel'))


	@commands.command()
	@checks.is_mod()
	async def muteall(self, ctx, user: Member):
		"""Mutes a user in all channels of this server."""
		for tchan in ctx.guild.text_channels:
			await tchan.set_permissions(user, reason=f"Mute in all channels by {ctx.author}", send_messages=False)
		await ctx.send(embed=self.bot.success(f'Member {user.name} muted in this guild'))


	@commands.command()
	@checks.is_mod()
	async def unmuteall(self, ctx, user: Member):
		"""Unmutes a user in all channels of this server."""
		for tchan in ctx.guild.text_channels:
			if tchan.overwrites_for(user) and not tchan.overwrites_for(user).is_empty():
				await tchan.set_permissions(user, reason=f"Unmute in all channels by {ctx.author}", send_messages=None)
		await ctx.send(embed=self.bot.success(f'Member {user.name} unmuted in this guild'))

	@commands.command(aliases=["cleanperms", "clearperms"])
	@checks.is_admin()
	async def pruneperms(self, ctx):
		"""Removes empty user-specific permission overrides from the server (manual channel permissions) ."""
		count = 0
		for tchan in ctx.guild.text_channels:
			for overwrite in tchan.overwrites:
				if overwrite[1].is_empty():
					await tchan.set_permissions(overwrite[0], overwrite=None)
					count += 1
		await ctx.send(embed=self.bot.success("No channel permission overwrites to clean up." if count == 0 else f"Cleaned up {count} channel permission overwrites."))

	@commands.command()
	@checks.is_mod()
	async def clearinvites(self, ctx, uses=1):
		"""Deletes invites from the invite list that have been used less than the number provided by uses. Will not delete any invite less than 1 hour old."""
		all_invites = await ctx.guild.invites()

		invites = [i for i in all_invites if i.uses <= uses and i.created_at < (datetime.utcnow()-timedelta(hours=1))]

		if not invites:
			await ctx.send(embed=self.bot.notice('I didn\'t find any invites matching your criteria'))
			return

		message = await ctx.send(embed=self.bot.success('Ok, a total of {} invites created by {} users with {} total uses would be pruned.'.format(
			                                             len(invites),
			                                             len({i.inviter.id for i in invites}),
			                                             sum(i.uses for i in invites))))

		await message.add_reaction('✅')
		await message.add_reaction('❌')

		def check(reaction, user):
			if user is None or user.id != ctx.author.id:
				return False

			if reaction.message.id != message.id:
				return False

			if reaction.emoji not in ['❌', '✅']:
				return False
			return True

		try:
			reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=120.0)
		except Exception as e:
			await ctx.send(embed=self.bot.success(str(e)))
			await message.clear_reactions()
			return

		if reaction.emoji != '✅':
			await ctx.send(embed=self.bot.error("Invites not cleared"))
			await message.clear_reactions()
			return

		for invite in invites:
			await invite.delete()
		await ctx.send(embed=self.bot.success("Invites cleared"))
		await message.clear_reactions()



def setup(bot):
	bot.add_cog(Moderation(bot))