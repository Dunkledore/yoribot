from discord.ext import commands
from discord import Embed


class Statistics:

	def __init__(self, bot):
		self.bot = bot
		if "Other" not in self.bot.categories:
			self.bot.categories["Other"] = [type(self).__name__]
		elif type(self).__name__ not in self.bot.categories["Admin and Moderation"]:
			self.bot.categories["Other"].append(type(self).__name__)

	async def on_command(self, ctx):
		query = "INSERT INTO statistics (guild_id, channel_id, author_id, prefix, command_name) VALUES ($1, $2, $3, $4, $5)"
		await self.bot.pool.execute(query, ctx.guild.id, ctx.channel.id, ctx.author.id, ctx.prefix, ctx.command.name)

	@commands.command()
	async def commands_stats(self, ctx, command):
		query = "SELECT author_id, channel_id FROM statistics WHERE (guild_id = $1) and (command_name = $2)"
		stats = await self.bot.pool.fetch(query, ctx.guild.id, command)
		author_stats = {}
		channel_stats = {}
		for stat in stats:
			author_id = stat['author_id']
			if author_id in author_stats:
				author_stats[author_id] += 1
			else:
				author_stats[author_id] = 1

			channel_id = stat['channel_id']
			if channel_id in channel_stats:
				author_stats[channel_id] += 1
			else:
				author_stats[channel_id] = 1


		for author in author_stats.keys():
			member = ctx.guild.get_user(author)
			if member:
				member = member.mention
			else:
				member = f'User : {author}'
			author_stats[member] = author_stats.pop(author)

		for channel_id in channel_stats.keys():
			channel = ctx.guild.get_channel(channel_id)
			if channel:
				channel = channel.mention
			else:
				channel = f'Channel : {channel_id}'
			channel_stats[channel] = author_stats.pop(channel_id)

		embed = Embed(title=f'Stats for {command} in {ctx.guild.name}')
		embed.add_field(name="Members", value='\n'.join([f'{mention} - {uses}' for mention, uses in author_stats.items()]))
		embed.add_field(name="Channels", value='\n'.join([f'{channel} - {uses}' for channel, uses in channel_stats.items()]))

		await ctx.send(embed=embed)



def setup(bot):
	bot.add_cog(Statistics(bot))