from discord.ext import commands
from ..utils import checks
from discord import Object
from datetime import datetime, timedelta
import asyncio


class Clear:
	"""Commands to delete messages, invites and redundant permissions. Requires mod perms"""

	def __init__(self, bot):
		self.bot = bot
		self.category = "Admin and Moderation"

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def clear(self, ctx, amount_to_delete: int):
		"""Clear a specified amount of messages from the channel the command is run in"""
		if amount_to_delete > 2000:
			await ctx.send(embed=self.bot.erorr("Too many messages to delete"))

		await ctx.channel.purge(limit=amount_to_delete)

	@commands.command(hidden=True)
	@checks.is_mod()
	@commands.guild_only()
	async def nuke(self, ctx):
		"""Clear 100 messages from the channel command is run in"""

		await ctx.channel.purge(limit=100)

	@commands.command(aliases=["clear_after"])
	@checks.is_mod()
	@commands.guild_only()
	async def clearafter(self, ctx, message_id: int, number_to_delete: int = 2000):
		"""Clear all messages (up to 2000) in the channel the command is run in after a given message id"""

		await ctx.channel.purge(limit=number_to_delete, after=Object(id=message_id))

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	@commands.cooldown(1, 20, commands.cooldowns.BucketType.guild)
	async def clearbefore(self, ctx, message_id: int, number_to_delete: int = 2000):
		"""Clear all messages (up to 2000) in the channel the command is run in before a given message id"""

		await ctx.channel.purge(limit=number_to_delete, before=Object(id=message_id))

	@clearbefore.error
	async def clearbeforeerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			if await checks.has_level(ctx, "developer"):
				await ctx.reinvoke()

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def clearbetween(self, ctx, before_message_id: int, after_message_id: int):
		"""Clear all messages (up to 2000) in the channel the command is run in between 2 given message ids"""

		await ctx.channel.purge(limit=2000, before=Object(id=before_message_id), after=Object(id=after_message_id))

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	@commands.cooldown(1, 20, commands.cooldowns.BucketType.guild)
	async def clearbot(self, ctx, number_to_delete: int = 2000):
		"""Clear specified number of messages (default 2000) from bots in the channel the command is run in."""

		def check(message):
			return message.author.bot

		await ctx.channel.purge(limit=number_to_delete, check=check)

	@clearbot.error
	async def clearboterror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			if await checks.has_level(ctx, "developer"):
				await ctx.reinvoke()

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def cleartext(self, ctx, number_to_delete: int = 2000):
		"""Clear specified number of messages (default 2000) containing only text in the channel the command is run in."""

		def check(message):
			return len(message.attachments) == 0

		await ctx.channel.purge(limit=number_to_delete, check=check)

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	async def clearimages(self, ctx, number_to_delete: int = 2000):
		"""Clear specified number of messages (default 2000) containing images in the channel the command is run in."""

		def check(message):
			has_image = False
			for attachment in message.attachments:
				if attachment.height:
					has_image = True
			return has_image

		await ctx.channel.purge(limit=number_to_delete, check=check)

	@commands.command()
	@checks.is_mod()
	@commands.guild_only()
	@commands.cooldown(1, 300, commands.cooldowns.BucketType.guild)
	async def cleargone(self, ctx):
		"""Clear all messages in all channels (up to 2000 per channel) from members no longer in the guild """

		def check(message):
			return message.author not in message.guild.members

		msg = await ctx.send(embed=self.bot.notice("Starting clearing. This could take some time..."))
		for channel in ctx.guild.text_channels:
			await channel.purge(limit=2000, check=check)
			await msg.edit(embed=self.bot.notice(f"Cleared {channel.mention}"))

		await msg.edit(embed=self.bot.success("Cleared all messages from non-members"))

	@cleargone.error
	async def cleargoneerror(self, ctx, error):
		if isinstance(error, commands.CommandOnCooldown):
			if await checks.has_level(ctx, "developer"):
				await ctx.reinvoke()

	@commands.command(aliases=["clearperms", "cleanperms"])
	@checks.is_mod()
	@commands.guild_only()
	async def pruneperms(self, ctx):
		"""Removes empty user-specific permission overrides from the server (manual channel permissions) ."""
		count = 0
		for tchan in ctx.guild.text_channels:
			for overwrite in tchan.overwrites:
				if overwrite[1].is_empty():
					await tchan.set_permissions(overwrite[0], overwrite=None)
					count += 1
		await ctx.send(embed=self.bot.success(
			f"Cleaned up {count} channel permission overwrites.") if count == 0 else self.bot.notice(
			"No channel permission overwrites to clean up."))

	@commands.command(aliases=["cleaninvites", "pruneinvites"])
	@checks.is_mod()
	@commands.guild_only()
	async def clearinvites(self, ctx, uses=1):
		"""Deletes invites from the invite list that have been used less than the number provided by uses. Will not delete any invite less than 1 hour old."""
		all_invites = await ctx.guild.invites()

		invites = [i for i in all_invites if i.uses <= uses and i.created_at < (datetime.utcnow()-timedelta(hours=1))]

		if not invites:
			await ctx.send(embed=self.bot.notice("I didn't find any invites matching your criteria"))
			return

		message = await ctx.send(embed=self.bot.succes(
			f"Ok, a total of {len(invites)} invites created by {len({i.inviter.id for i in invites})} users with {sum(i.uses for i in invites)} total uses would be pruned."))

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

		reaction = None
		try:
			reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=120.0)
		except asyncio.TimeoutError as e:
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
	bot.add_cog(Clear(bot))
