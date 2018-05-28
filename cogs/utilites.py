from discord.ext import commands
from .utils.paginator import HelpPaginator, Pages
from discord import Permissions, utils


class Utilities:
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def help(self, ctx, *, cog_or_command=None):
		"""Show's a list of cogs, or information about a cog, or information about a command"""
		if not cog_or_command:
			cogs = []
			for command in self.bot.commands:
				if command.cog_name not in cogs:
					cogs.append(command.cog_name)
			pager = Pages(ctx, entries=cogs)
		else:
			cog = self.bot.get_cog(cog_or_command)
			if cog:
				pager = HelpPaginator.from_cog(ctx, cog)
			else:
				command = self.bot.get_command()
				pager = HelpPaginator.from_command(ctx, command)

		await pager.paginate()

	@commands.command(aliases=['invite'])
	async def join(self, ctx):
		"""Provides the bot invite link."""
		perms = Permissions.none()
		perms.read_messages = True
		perms.external_emojis = True
		perms.send_messages = True
		perms.manage_roles = True
		perms.manage_channels = True
		perms.ban_members = True
		perms.kick_members = True
		perms.manage_messages = True
		perms.embed_links = True
		perms.read_message_history = True
		perms.attach_files = True
		perms.add_reactions = True
		await ctx.send(f'<{utils.oauth_url(self.bot.client_id, perms)}>')


def setup(bot):
	bot.add_cog(Utilities(bot))
