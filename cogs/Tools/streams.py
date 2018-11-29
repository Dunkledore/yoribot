from discord.ext import commands
from discord import Role, Streaming, Forbidden, Embed, TextChannel
from ..utils import checks
import asyncpg
import aiohttp
import traceback
import asyncio


class WatchingStream:

	def __init__(self, channel, close_on_end, user_login):
		self.channel = channel
		self.user_login = user_login
		self.close_on_end = close_on_end
		self.stream_data = None
		self.message = None
		self.live = False

		async def make_live(self, data):
			self.stream_data = data
			if self.live:
				await self.message.edit(embed=self.stream_embed(self.stream_data))
			else:
				self.message = await self.channel.send(embed=self.stream_embed(self.stream_data))
			self.live = True

		async def make_not_live(self):
			self.stream_data = None
			if close_on_end:
				if self.message:
					try:
						await self.message.delete()
					except Forbidden:
						pass
			self.live = False

		def stream_embed(stream_data):
			return Embed(title=stream_data["title"])


class Stream:

	def __init__(self, bot):
		self.bot = bot
		self.headers = None
		self.bot.loop.create_task(self.set_client_id())
		self.twitch_base = "https://api.twitch.tv/helix/"
		self.watching_streams = []
		self.online_streams = []

	async def load_watching_streams(self):
		await self.bot.wait_until_ready()
		query = "SELECT * FROM streams"
		streams = await self.bot.pool.fetch(query)
		for stream in streams:
			channel = await self.bot.get_channel(stream["channel_id"])
			if not channel:
				continue
			user_login = stream['user_login']
			self.watching_streams.append(WatchingStream(channel, stream["close_on_end"], user_login))

	async def cycle_streams(self):

		while True:
			if self.watching_streams:
				try:
					watching_stream_chunks = [self.watching_streams[x:x+100] for x in
					                          range(0, len(self.watching_streams),
					                                100)]  # Twitch only allows 100 at a time

					online_streams = []  # Turns the chunks into a list of online streams containing raw data from twitch
					for chunk in watching_stream_chunks:
						logins = [stream.user_login for stream in chunk]
						params = [("user_login", login) for login in logins]
						data = await self.make_request("stream", params)
						online_streams.extend(data)

					online_streams_objects = []  # Turns the raw data into a list of objects
					for online_stream in online_streams:
						user_login = online_stream['user_name']
						watching_streams = [watching_stream for watching_stream in self.watching_streams if
						                    watching_stream.user_login == user_login]
						for watching_stream in watching_streams:
							watching_stream.make_live(online_stream)
							online_streams_objects.append(watching_stream)

					streams_to_make_offline = set(self.online_streams)-set(
						online_streams_objects)  # Take the old stream objects and subtracts the new to leave the ones that stopped
					for stream in streams_to_make_offline:
						stream.make_not_live()

					self.online_streams = online_streams_objects
				except Exception as e:
					traceback_text = "\n".join(traceback.format_exception(type(e), e, e.__traceback__, 4))
					await self.bot.error_hook.send(
						embed=Embed(title="Error From Stream Cycle", description=traceback_text))

			await asyncio.sleep(30)

	async def set_client_id(self):
		query = "SELECT client_id FROM twitch"
		id = self.bot.pool.fetchval(query)
		if id:
			self.headers = {"client_id": id}

	async def get_game_data_by_id(self, id):
		return await self.make_request("games", {"id": id})

	async def make_request(self, endpoint, params=None):
		async with aiohttp.ClientSession() as cs:
			async with cs.get("https://api.twitch.tv/helix/", params=params) as r:
				return await r.json()

	@commands.command()
	@checks.is_admin()
	async def watch_stream(self, ctx, stream_name, channel: TextChannel, delete_on_close=False):
		query = "INSERT INTO streams (user_login, channel_id, delete_on_close) VALUES ($1,$2,$3)"
		await self.bot.pool.execute(query, stream_name, channel.id, delete_on_close)
		self.watching_streams.append(WatchingStream(channel, delete_on_close, stream_name))

	@commands.command()
	@checks.is_admin()
	async def streamrole(self, ctx, role: Role = None):
		"""Set the role to apply to a member when they start streaming. Leave role blank to turn off"""

		if not Role:
			query = "DELETE FROM streamrole WHERE guild_id = %1"
			await self.bot.pool.execute(query, ctx.guild.id)
			await ctx.send(embed=self.bot.success(
				"Stream role turned off. I will no longer apply a role when a member is streaming"))
		else:
			if not ctx.me.guild_permissions.manage_roles:
				await ctx.send(
					embed=self.bot.error("Grant me the Manage Roles permission and then call this command again"))
			if ctx.me.top_role < role:
				await ctx.send(embed=self.bot.error(
					"This role is higher than me highest role. Move it below and then run the command again"))
			insertquery = "INSERT INTO streamrole (guild_id, role_id) VALUES ($1, $2)"
			updatequery = "UPDATE streamrole SET role_id = $1, WHERE guild_id = $2"
			try:
				await self.bot.pool.execute(insertquery, ctx.guild.id, role.id)
			except asyncpg.UniqueViolationError:
				await self.bot.pool.execute(updatequery, role.id, ctx.guild.id)

			await ctx.send(embed=self.bot.success(f"Role set to {role.mention}"))

	async def on_member_update(self, before, after):

		before_streaming = None
		for activity in before.activities:
			if isinstance(activity, Streaming):
				before_streaming = activity

		after_streaming = None
		for activity in after.activities:
			if isinstance(activity, Streaming):
				after_streaming = activity

		if not any([before_streaming, after_streaming]):
			return

		query = "SELECT role_id FROM streamrole WHERE guild_id = $1"
		role_id = self.bot.pool.fetchval(query, after.guild.id)
		if not role_id:
			return
		role = after.guild.get_role(role_id)
		if not role:
			return

		if before_streaming and not after_streaming:
			try:
				await after.remove_roles(role, reason="Yori: Stopped Streaming")
			except Forbidden:
				pass
			return

		if after_streaming and not before_streaming:
			try:
				await after.add_roles(role, reason="Yori:Started Streaming")
			except Forbidden:
				pass
			return


def setup(bot):
	bot.add_cog(Stream(bot))