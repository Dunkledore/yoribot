from discord.ext import commands
from discord import Embed

class LFG:

	def __init__(self,bot):
		self.bot = bot


	@commands.command()
	async def whoplays(self, ctx, game):
		players = []
		for member in ctx.guild.members:
			for activ in member.activities + [member.activity]:
				if activ.name == game:
					players.append(member)
		if not players:
			embed = self.bot.error("No players playing this game")
		else:
			embed = Embed(title=f"Players playing {game}", description="\n".join([member.name for member in players]))

		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(LFG(bot))