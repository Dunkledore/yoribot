from discord.ext import commands
from .utils import checks
from discord import TextChannel, Embed

class GiveAway:

	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=["give_away"])
	@commands.guild_only()
	@checks.is_admin()
	async def giveaway(self, ctx, item, channel: TextChannel = None):
		query = "SELECT item from giveaway WHERE guild_id = $1"
		db_item = await self.bot.pool.fetchval(query, ctx.guild.id)
		if db_item:
			await ctx.send(embed=self.bot.error(f"You already have a giveaway running for {db_item} please use {ctx.prefix}endgiveaway"))
			return

		if not channel:
			channel = ctx.channel

		embed = Embed(title="Give away started", description=f"React to this message with 🎉 to be in with a chance of winning {item} ")

		message = await channel.send(embed=embed)

		query = "INSERT INTO giveaway (guild_id, item, message_id, channel_id) VALUES ($1, $2, $3, $4)"
		await self.bot.pool.execute(query, ctx.guild.id, item, message.id, channel.id)

	@commands.command(aliases=["giveawayend", "end_giveaway"])
	@commands.guild_only()
	@checks.is_admin()
	async def endgiveaway(self, ctx):
		query = "SELECT * FROM giveaway WHERE guild_id = $1"
		results = await self.bot.pool(query, ctx.guild.id)
		if not results:
			await ctx.send(embed=self.bot.errro("There is no giveaway for this guild"))
			return

		channel = await self.bot.get_channel(results["channel_id"])
		if not channel:
			await ctx.send(embed=self.bot.error("The channel the giveaway was posted in could not be found"))

		message = await channel.get_message(results["message_id"])
		if not message:
			await ctx.send(embed=self.bot.error("The message could not be found"))

		reaction =





def setup(bot):
	bot.add_cog(GiveAway(bot))