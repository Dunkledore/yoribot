from discord.ext import commands
from .utils import checks
from datetime import datetime, timedelta

class Clear:

	def __init__(self, bot):
		self.bot = bot


	@commands.command()
	@checks.is_mod()
	async def clear(self, ctx, number_to_delete):
		if number_to_delete > 2000:
			await ctx.send(embed=self.bot.erorr("Too many messages to delete"))

		await ctx.channel.purge(limit=100)

	@commands.command()
	@checks.is_mod()
	async def nuke(self, ctx):

		await ctx.channel.purge(limit=100)

	@commands.command()
	@checks.is_mod()
	async def clearafter(self, ctx, message_id, number_to_delete=2000):

		await ctx.channel.purge(limit=number_to_delete, after=message_id)


	@commands.command()
	@checks.is_mod()
	async def clearbefore(self, ctx, message_id, number_to_delete=2000):

		await ctx.channel.purge(limit=number_to_delete, before=message_id)

	@commands.command()
	@checks.is_mod()
	async def clearbetween(self, ctx, before_message_id, after_message_id):

		await ctx.channel.purge(limit=2000, before=before_message_id, after=after_message_id)

	@commands.command()
	@checks.is_mod()
	async def clearbot(self, ctx, number_to_delete = 2000):
		def check(message):
			return message.author.bot

		await ctx.channel.purge(limit=number_to_delete, check=check)

	@commands.command()
	@checks.is_mod()
	async def clearbot(self, ctx, number_to_delete = 2000):
		def check(message):
			return message.author.bot

		await ctx.channel.purge(limit=number_to_delete, check=check)

	@commands.command()
	@checks.is_mod()
	async def cleargone(self, ctx):
		def check(message):
			return message.author in message.guild.members

		for channel in ctx.guild.textchannels:
			await channel.purge(limit=2000, check=check)

	@commands.command(aliases=["clearperms", "cleanperms"])
	@checks.is_admin()
	async def pruneperms(self, ctx):
		"""Removes empty user-specific permission overrides from the server (manual channel permissions) ."""
		count = 0
		for tchan in ctx.guild.text_channels:
			for overwrite in tchan.overwrites:
				if overwrite[1].is_empty():
					await tchan.set_permissions(overwrite[0], overwrite=None)
					count += 1
		await ctx.send(embed=self.bot.success(f"Cleaned up {count} channel permission overwrites.") if count == 0 else self.bot.notice("No channel permission overwrites to clean up."))

	@commands.command(aliases=["cleaninvites", "pruneinvites"])
	@checks.is_mod()
	async def clearinvites(self, ctx, uses=1):
		"""Deletes invites from the invite list that have been used less than the number provided by uses. Will not delete any invite less than 1 hour old."""
		all_invites = await ctx.guild.invites()

		invites = [i for i in all_invites if i.uses <= uses and i.created_at < (datetime.utcnow()-timedelta(hours=1))]

		if not invites:
			await ctx.send(embed=self.bot.notice("I didn't find any invites matching your criteria"))
			return

		message = await ctx.send(embed=self.bot.succes(f"Ok, a total of {len(invites)} invites created by {len({i.inviter.id for i in invites})} users with {sum(i.uses for i in invites)} total uses would be pruned."))

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
	bot.add_cog(Clear(bot))