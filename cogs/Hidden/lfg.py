from discord import Object
from ..utils import checks

class LFG:

	def __init__(self, bot):
		self.bot = bot


	async def on_reaction_add(self, reaction, user):
		if reaction.emoji != "✨":
			return
		if reaction.message.guild.id != 250309924096049164:
			return
		proxy_ctx = Object(id=None)
		proxy_ctx.guild = reaction.message.guild
		proxy_ctx.author = user
		proxy_ctx.bot = self.bot
		if not await checks.has_level(proxy_ctx, "mod"):
			return
		role = reaction.message.guild.get_role(346083000372428811)
		await self.bot.error_hook.send(role)
		await reaction.message.author.add_roles(role)

def setup(bot):
	bot.add_cog(LFG(bot))