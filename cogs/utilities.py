from discord.ext import commands
from .utils.paginator import HelpPaginator, Pages
from discord import Permissions, utils


class Utilities:
	def __init__(self, bot):
		self.bot = bot
		self.bot.remove_command("help")
		if "Other" not in self.bot.categories:
			self.bot.categories["Other"] = [type(self).__name__]
		elif type(self).__name__ not in self.bot.categories["Other"]:
			self.bot.categories["Other"].append(type(self).__name__)


	@commands.command()
	async def help(self, ctx, *, cog_or_command_or_category=None):
		"""Show's a list of cogs, or information about a cog, or information about a command"""



		if not cog_or_command_or_category:
			entries = list(self.bot.categories.keys())
			pager = Pages(ctx, entries=entries)


			async def numbered_page(number):
				actual_page = pager.current_page * number
				category_name = pager.entries[actual_page-1]
				await pager.message.delete()
				await ctx.invoke(ctx.command, cog_or_command_or_category=category_name)
			next_page = [('\N{BLACK RIGHT-POINTING TRIANGLE}', pager.next_page)]
			previous_page = [('\N{BLACK LEFT-POINTING TRIANGLE}', pager.previous_page)]
			stop_pager = [('\N{BLACK SQUARE FOR STOP}', pager.stop_pages)]
			reaction_emojis = [("1\u20e3", lambda: numbered_page(1)),
			                ("2\u20e3", lambda: numbered_page(2)),
			                ("3\u20e3", lambda: numbered_page(3)),
			                ("4\u20e3", lambda: numbered_page(4)),
			                ("5\u20e3", lambda: numbered_page(5)),
			                ("6\u20e3", lambda: numbered_page(6)),
			                ("7\u20e3", lambda: numbered_page(7)),
			                ("8\u20e3", lambda: numbered_page(8)),
			                ("9\u20e3", lambda: numbered_page(9))]

			pager.paginating = True
			show_page_controls = len(entries) > 9
			pager.reaction_emojis = (previous_page if show_page_controls else []) + reaction_emojis[:len(entries)] + (next_page if show_page_controls else []) + stop_pager
		else:
			if cog_or_command_or_category in self.bot.categories:
				entries = self.bot.categories[cog_or_command_or_category]
				pager = Pages(ctx, entries=entries)

				async def numbered_page(number):
					actual_page = pager.current_page*number
					cog_name = pager.entries[actual_page-1]
					await pager.message.delete()
					await ctx.invoke(ctx.command, cog_or_command_or_category=cog_name)

				next_page = [('\N{BLACK RIGHT-POINTING TRIANGLE}', pager.next_page)]
				previous_page = [('\N{BLACK LEFT-POINTING TRIANGLE}', pager.previous_page)]
				stop_pager = [('\N{BLACK SQUARE FOR STOP}', pager.stop_pages)]
				reaction_emojis = [("1\u20e3", lambda: numbered_page(1)),
				                   ("2\u20e3", lambda: numbered_page(2)),
				                   ("3\u20e3", lambda: numbered_page(3)),
				                   ("4\u20e3", lambda: numbered_page(4)),
				                   ("5\u20e3", lambda: numbered_page(5)),
				                   ("6\u20e3", lambda: numbered_page(6)),
				                   ("7\u20e3", lambda: numbered_page(7)),
				                   ("8\u20e3", lambda: numbered_page(8)),
				                   ("9\u20e3", lambda: numbered_page(9))]

				show_page_controls = len(entries) > 9
				pager.reaction_emojis = (previous_page if show_page_controls else []) + reaction_emojis[:len(entries)] + (next_page if show_page_controls else []) + stop_pager
				pager.paginating = True

			else:
				cog = self.bot.get_cog(cog_or_command_or_category)
				if cog:
					pager = await HelpPaginator.from_cog(ctx, cog)
				else:
					command = self.bot.get_command()
					pager = await HelpPaginator.from_command(ctx, command)

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