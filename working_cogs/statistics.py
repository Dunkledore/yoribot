from discord.ext import commands
from discord import Embed, Colour
import psutil


class Statistics:

	def __init__(self, bot):
		self.bot = bot
		self.category = "Misc"
		self.process = psutil.Process()

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
				channel_stats[channel_id] += 1
			else:
				channel_stats[channel_id] = 1

		for author in list(author_stats.keys()):
			member = self.bot.get_user(author)
			if member:
				member = member.mention
			else:
				member = f'User : {author}'
			author_stats[member] = author_stats.pop(author)

		for channel_id in list(channel_stats.keys()):
			channel = self.bot.get_channel(channel_id)
			if channel:
				channel = channel.mention
			else:
				channel = f'Channel : {channel_id}'
			channel_stats[channel] = channel_stats.pop(channel_id)

		embed = Embed(title=f'Stats for prefix in {ctx.guild.name}')
		embed.add_field(name="Members",
		                value='\n'.join([f'{mention} - {uses}' for mention, uses in author_stats.items()]))
		embed.add_field(name="Channels",
		                value='\n'.join([f'{channel} - {uses}' for channel, uses in channel_stats.items()]))

		await ctx.send(embed=embed)


@commands.command()
async def about(self, ctx):
	"""Tells you information about the bot itself."""

	embed = Embed()
	embed.title = 'About Yori Bot'
	embed.url = 'http://yoribot.com'
	embed.colour = Colour.blurple()

	embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url)

	# statistics
	total_members = sum(1 for _ in self.bot.get_all_members())
	total_online = len({m.id for m in self.bot.get_all_members() if m.status is discord.Status.online})
	total_unique = len(self.bot.users)

	voice_channels = []
	text_channels = []
	for guild in self.bot.guilds:
		voice_channels.extend(guild.voice_channels)
		text_channels.extend(guild.text_channels)

	text = len(text_channels)
	voice = len(voice_channels)

	embed.add_field(name='Members', value=f'{total_members} total\n{total_unique} unique\n{total_online} unique online')
	embed.add_field(name='Channels', value=f'{text + voice} total\n{text} text\n{voice} voice')

	memory_usage = self.process.memory_full_info().uss/1024**2
	cpu_usage = self.process.cpu_percent()/psutil.cpu_count()
	embed.add_field(name='Process', value=f'{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU')

	embed.add_field(name='Guilds', value=len(self.bot.guilds))
	embed.add_field(name='Commands Run', value=sum(self.bot.command_stats.values()))
	embed.add_field(name='Website', value="[http://yoribot.com](http://yoribot.com)")
	embed.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')
	await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(Statistics(bot))