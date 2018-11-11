import discord


class Stream:

	def __init__(self, bot):
		self.bot = bot

	async def on_member_update(self, before, after):
		if before.activity == after.activity:
			return

		if (not isinstance(before.activity, discord.Streaming)) or (not isinstance(after.activity, discord.Streaming)):
			return




def setup(bot):
	bot.add_cog(Stream(bot))