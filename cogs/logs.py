from discord.ext import commands
from .utils import checks


class Logs:

	def __init__(self, bot):
		self.bot = bot
		if "Admin and Moderation" not in self.bot.categories:
			self.bot.categories["Admin and Moderation"] = [type(self).__name__]
		elif type(self).__name__ not in self.bot.categories["Admin and Moderation"]:
			self.bot.categories["Admin and Moderation"].append(type(self).__name__)


	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def member_log_channel(self,ctx):
		"""Set the channel for member logs"""
		pass

	@commands.command()
	@commands.guild_only()
	@checks.is_admin()
	async def message_log_channel(self,ctx):
		"""Set the channel for message logs"""
		pass


def setup(bot):
	bot.add_cog(Logs(bot))