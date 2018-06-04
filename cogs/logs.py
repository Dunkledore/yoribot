from discord.ext import commands
from .utils import checks, utils
from discord import TextChannel, Embed
import asyncpg
import datetime


class Logs:

	def __init__(self, bot):
		self.bot = bot
		if "Admin and Moderation" not in self.bot.categories:
			self.bot.categories["Admin and Moderation"] = [type(self).__name__]
		elif type(self).__name__ not in self.bot.categories["Admin and Moderation"]:
			self.bot.categories["Admin and Moderation"].append(type(self).__name__)

	# Commands

	@commands.command()
	@checks.is_admin()
	async def start_message_logs(self, ctx, channel: TextChannel):

		insertquery = "INSERT INTO logs (guild_id, message_log_channel_id VALUES ($1, $2)"
		alterquery = "UPDATE logs SET message_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, ctx.guild.id, channel.id)

		await ctx.send(embed=self.bot.success(f'Now sending message logs to {channel.mention}. To stop sending message '
		                                      f'logs, delete the channel '))

	@commands.command()
	@checks.is_admin()
	async def start_member_logs(self, ctx, channel: TextChannel):

		insertquery = "INSERT INTO logs (guild_id, member_log_channel_id VALUES ($1, $2)"
		alterquery = "UPDATE logs SET member_log_channel_id = $1 WHERE guild_id = $2"

		try:
			await self.bot.pool.execute(insertquery, ctx.guild.id, channel.id)
		except asyncpg.UniqueViolationError:
			await self.bot.pool.execute(alterquery, ctx.guild.id, channel.id)

		await ctx.send(embed=self.bot.success(f'Now sending member logs to {channel.mention}. To stop sending message '
		                                      f'logs, delete the channel '))

	async def on_guild_channel_delete(self, channel):  # Kind of like and auto firing commands
		member_query = "UPDATE logs SET member_log_channel_id = $1 WHERE member_log_channel_id = $2"
		message_query = "UPDATE logs SET message_log_channel_id = $1 WHERE member_log_channel_id = $2"

		await self.bot.pool.execute(member_query, None, channel.id)
		await self.bot.pool.execute(message_query, None, channel.id)

	async def on_member_join(self, member):

		query = "SELECT member_log_channel_id FROM logs WHERE guild_id = $1"
		log_channel_id = await self.bot.pool.fetchval(query)
		if not log_channel_id:
			return
		log_channel = self.bot.get_channel(log_channel_id)
		if not log_channel:
			return

		embed = Embed(title="📥 Member Join", description=member.mention)
		embed.timestamp = datetime.datetime.utcnow()
		embed.set_footer(text='Joined')
		embed.set_author(name=member.name, icon_url=member.avatar_url)
		embed.add_field(name='ID', value=member.id)
		embed.add_field(name='Joined', value=member.joined_at)
		embed.add_field(name='Created', value=utils.human_timedelta(member.created_at), inline=False)
		embed.set_thumbnail(url=member.avatar_url)

		



	async def on_member_remove(self, member):
		pass

	async def on_member_ban(self, guild, user):
		pass

	async def on_member_unban(self, guild, user):
		pass

	async def on_message_delete(self, message):
		pass

	async def on_message_edit(self, before, after):
		pass



def setup(bot):
	bot.add_cog(Logs(bot))
