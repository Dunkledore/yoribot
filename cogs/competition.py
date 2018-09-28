from discord import TextChannel
import asyncpg


class Competition:

	def __init__(self, bot):
		self.bot = bot

	async def start_competiton(self, ctx, name, channel: TextChannel):
		"""Start a competition in the given channel"""
		query = "INSERT INTO competition (channel_id, name) VALUES ($1, $2)"
		try:
			await self.bot.pool.execute(query, channel.id, name)
			embed = self.bot.success(f"{name} started in {channel.mention}")
			embed.set_footer(
				text=f"Use {ctx.prefix}end_competition {channel.mention} to end the competition and announce a winner")
			await ctx.send(embed=embed)
		except asyncpg.UniqueViolationError:
			await ctx.send(embed=self.bot.error("There is already a competition happening in this channel"))

	async def end_competition(self, ctx, channel: TextChannel):
		"""End an already running competition"""

		query = "SELECT created FROM competition WHERE channel_id = $1"
		created = await self.bot.pool.fetchval(query, channel.id)
		if not created:
			await ctx.send(embed=self.bot.error("No competition in the channel"))
			return

		candidates = []
		async for message in channel.history(limit=5000, after=created):
			if message.attachements:
				if message.attachments[0].height:
					candidates.append(message)

		candidates_votes = {}
		for message in candidates:
			votes = 0
			for reaction in message.reactions:
				if reaction.emoji == "⬇":
					votes -= 1
				if reaction.emoji == "⬆":
					votes += 1
			candidates_votes[message] = votes

		ordered = []
		for message in sorted(candidates_votes, key=candidates_votes.get, reverse=True):
			ordered.append({message: candidates_votes[message]})

		await ctx.send(embed=self.bot.success(f"And the winnder is {ordered[0].author.name}"))


def setup(bot):
	bot.add_cog(Competition(bot))
