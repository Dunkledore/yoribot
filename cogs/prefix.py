from discord.ext import commands
from discord import Embed
from .utils import checks


class Prefix:

	def __init__(self, bot):
		self.bot = bot
		if "Admin" not in self.bot.categories:
			self.bot.categories["Admin"] = [type(self).__name__]
		elif type(self).__name__ not in self.bot.categories["Admin"]:
			self.bot.categories["Admin"].append(type(self).__name__)


	async def __local_check(self, ctx):
		if str(ctx.guild.id) not in self.bot.prefixes:
			self.bot.prefixes[str(ctx.guild.id)] = []
		return True

	@commands.group()
	@commands.guild_only()
	@checks.is_admin()
	async def prefix(self, ctx):
		"""See the prefixes for the guild"""
		if str(ctx.guild.id) not in self.bot.prefixes:
			self.bot.prefixes[str(ctx.guild.id)] = []

		if not ctx.invoked_subcommand:
			base_prefixes = [f"<@{self.bot.user.id}>"]
			prefixes = self.bot.prefixes[str(ctx.guild.id)]
			if not prefixes:
				usable_prefixes = base_prefixes
				usable_prefixes.append("*")
			else:
				usable_prefixes = base_prefixes + prefixes
			embed = Embed(title=f"Prefixes for {ctx.guild.name}", description="\n".join(usable_prefixes))
			await ctx.send(embed=embed)

	@commands.command(aliases=['prefix_add'])
	@commands.guild_only()
	@checks.is_mod()
	async def add_prefix(self, ctx, *, prefix):
		"""Adds a guild prefix"""

		if prefix in self.bot.prefixes[str(ctx.guild.id)]:
			await ctx.send(embed=self.bot.notice("This is already a prefix"))
		elif prefix in [f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"]:
			await ctx.send(embed=self.bot.notice("Yori will always respond to being mentioned by default"))
		else:
			self.bot.prefixes[str(ctx.guild.id)].append(prefix)
			self.bot.save_prefixes()
			await ctx.send(embed=self.bot.success(f"{prefix} added"))

	@commands.command(aliases=['delete_prefix', 'prefix_delete', 'prefix_remove'])
	@checks.is_admin()
	@commands.guild_only()
	async def remove_prefix(self, ctx, *, prefix):
		"""Removes a guild prefix"""

		if prefix not in self.bot.prefixes[str(ctx.guild.id)]:
			await ctx.send(embed=self.bot.notice("This is not a prefix"))
		elif prefix in [f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"]:
			await ctx.send(embed=self.bot.notice("Yori will always respond to being mentioned by default"))
		else:
			self.bot.prefixes[str(ctx.guild.id)].remove(prefix)
			self.bot.save_prefixes()
			await ctx.send(embed=self.bot.success(f"{prefix} removed"))

def setup(bot):
	bot.add_cog(Prefix(bot))
