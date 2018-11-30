from discord.ext import commands
from discord import Role, Streaming, Forbidden, Embed, TextChannel
from ..utils import checks
import asyncpg
import aiohttp
import traceback
import asyncio


class WatchingStream:

	def __init__(self, channel, delete_on_close, user_login, guild_id):
		self.channel = channel
		self.user_login = user_login
		self.delete_on_close = delete_on_close
		self.stream_data = None
		self.message = None
		self.live = False
		self.guild_id = guild_id

	async def make_live(self, data):
		self.stream_data = data
		if self.live:
			await self.message.edit(embed=self.stream_embed(self.stream_data))
		else:
			self.message = await self.channel.send(embed=self.stream_embed(self.stream_data))
		self.live = True

	async def make_not_live(self):
		self.stream_data = None
		if self.delete_on_close:
			if self.message:
				try:
					await self.message.delete()
					self.message = None
				except Forbidden:
					pass
		self.live = False

	def stream_embed(self, stream_data):
		return Embed(title=stream_data["title"])

	def __hash__(self):
		return hash((self.channel.id, self.user_login))

	def __eq__(self, other):
		return (self.user_login == other.user_login) and (self.channel.id == other.channel.id)

	def __ne__(self, other):
		return not self.__eq__(other)

	def __str__(self):
		return f"{self.user_login} : {self.channel.mention}"

	def __repr__(self):
		return self.__str__() + f" : {self.guild_id}"






class Stream:

	def __init__(self, bot):
		self.bot = bot
		self.headers = None
		self.bot.loop.create_task(self.set_client_id())
		self.twitch_base = "https://api.twitch.tv/helix/"
		self.watching_streams = []
		self.bot.loop.create_task(self.load_watching_streams())
		self.online_streams = []
		self.bot.loop.create_task(self.cycle_streams())

	async def load_watching_streams(self):
		await self.bot.wait_until_ready()
		query = "SELECT * FROM streams"
		streams = await self.bot.pool.fetch(query)
		for stream in streams:
			channel = self.bot.get_channel(stream["channel_id"])
			if not channel:
				continue
			user_login = stream['user_login']
			self.watching_streams.append(WatchingStream(channel, stream["delete_on_close"], user_login, stream['guild_id']))

	async def cycle_streams(self):
		while True:
			if self.watching_streams:
				try:
					watching_stream_chunks = [self.watching_streams[x:x+100] for x in
					                          range(0, len(self.watching_streams),
					                                100)]  # Twitch only allows 100 at a time

					online_streams = []  # Turns the chunks into a list of online streams containing raw data from twitch
					print(watching_stream_chunks)
					for chunk in watching_stream_chunks:
						logins = [stream.user_login for stream in chunk]
						params = [("user_login", login) for login in logins]
						data = await self.make_request("streams", params)
						print(params)
						online_streams.extend(data["data"])

					print(online_streams)

					online_streams_objects = []  # Turns the raw data into a list of objects
					for online_stream in online_streams:
						user_login = online_stream["user_name"]
						watching_streams = [watching_stream for watching_stream in self.watching_streams if
						                    watching_stream.user_login.lower() == user_login.lower()]
						for watching_stream in watching_streams:
							await watching_stream.make_live(online_stream)
							online_streams_objects.append(watching_stream)

					streams_to_make_offline = set(self.online_streams)-set(
						online_streams_objects)  # Take the old stream objects and subtracts the new to leave the ones that stopped
					for stream in streams_to_make_offline:
						await stream.make_not_live()

					self.online_streams = online_streams_objects
				except Exception as e:
					traceback_text = "\n".join(traceback.format_exception(type(e), e, e.__traceback__, 4))
					await self.bot.error_hook.send(
						embed=Embed(title="Error From Stream Cycle", description=traceback_text))

			await asyncio.sleep(30)

	async def set_client_id(self):
		query = "SELECT client_id FROM twitch"
		id = await self.bot.pool.fetchval(query)
		if id:
			self.headers = {"client-id": id}

	async def get_game_data_by_id(self, id):
		return await self.make_request("games", {"id": id})

	async def make_request(self, endpoint, params=None):
		async with aiohttp.ClientSession() as cs:
			async with cs.get(f"https://api.twitch.tv/helix/{endpoint}", params=params, headers=self.headers) as r:
				return await r.json()

	@commands.command()
	@checks.is_admin()
	async def view_streams(self, ctx):
		streams = [watching_stream for watching_stream in self.watching_streams if watching_stream.guild_id == ctx.guild.id]
		embed = Embed(title=f"Stream watched in {ctx.guild.name}", description="\n".join([str(stream) for stream in streams]))
		await ctx.send(embed=embed)

	@commands.command()
	@checks.is_admin()
	async def watch_stream(self, ctx, stream_name, channel: TextChannel, delete_on_close=False):
		stream_object = WatchingStream(channel, delete_on_close, stream_name, ctx.guild.id)
		if stream_object in self.watching_streams:
			await ctx.send(embed=self.bot.error("Alreayd watching this stream in this channel"))
			return

		query = "INSERT INTO streams (user_login, channel_id, delete_on_close, guild_id) VALUES ($1,$2,$3,$4)"
		await self.bot.pool.execute(query, stream_name, channel.id, delete_on_close, ctx.guild.id)
		self.watching_streams.append(stream_object)
		await ctx.send(embed=self.bot.success(f"Watching {stream_name} in {channel.mention}"))

	@commands.command()
	@checks.is_admin()
	async def unwatch_stream(self, ctx, stream_name, channel: TextChannel = None):

		if channel:
			matching_streams = [watching_stream for watching_stream in self.watching_streams if
			                    (watching_stream.channel_id == channel.id) and (
						                    watching_stream.user_login == stream_name)]
			if not matching_streams:
				await ctx.send(embed=self.bot.error("Not watching that stream in this channel"))
				return
			query = "DELETE FROM streams WHERE (user_login = $1) and (channel_id = $2)"
			await self.bot.pool.execute(query, stream_name, channel.id)
			for stream in matching_streams:
				self.watching_streams.remove(stream)
			await ctx.send(embed=self.bot.success(f"No longer watching {stream_name} in {channel.mention}"))
		else:
			matching_streams = [watching_stream for watching_stream in self.watching_streams if
			                    (watching_stream.guild_id == ctx.guild.id) and (
						                    watching_stream.user_login == stream_name)]
			if not matching_streams:
				await ctx.send(embed=self.bot.error("Not watching that stream in this guild"))
				return
			query = "DELETE FROM streams WHERE (user_login = $1) and (guild_id = $2)"
			await self.bot.pool.execute(query, stream_name, ctx.guild.id)
			for stream in matching_streams:
				self.watching_streams.remove(stream)
			await ctx.send(embed=self.bot.success(f"No longer watching {stream_name} in any channel"))

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
