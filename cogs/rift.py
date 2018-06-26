from discord.ext import commands
from discord import TextChannel, Embed
from .utils import checks
import re

class Rift:

	def __init__(self, bot):
		self.bot = bot
		self.rift_name_cache = {}
		self.rift_channel_cache = {}
		self.bot.loop.create_task(self.update_cache())

	@staticmethod
	def formatembed(message):
		em = Embed(color=message.author.color, description=message.content)
		avatar = message.author.avatar_url
		author_name = message.author.nick+" ("+message.author.name+")" if message.author.nick else message.author.name
		em.set_author(name=author_name, icon_url=avatar)
		footer = "- sent by "+str(message.author.id)+" from #"+message.channel.name+" in "+message.guild.name
		if len(message.attachments) == 1:
			for attachment in message.attachments:
				if re.match(r"([a-z\-_0-9\/\:\.]*\.(jpg|jpeg|png|gif))", attachment.filename,
				            re.IGNORECASE) is not None:
					em.set_image(url=attachment.proxy_url)
		em.set_footer(text=footer)
		return em

	async def update_cache(self):
		await self.bot.wait_until_ready()
		query = "SELECT * FROM rift"
		results = await self.bot.pool.fetc(query)

		for result in results:
			self.rift_name_cache[results["rift_name"]] = dict(result)
			for channel in result["channels"]:
				if channel.id in self.rift_channel_cache:
					self.rift_channel_cache[channel.id].append(result["rift_name"])

	@checks.is_admin()
	@commands.command()
	async def create_rift(self, ctx, rift_name, initial_channel: TextChannel = None):
		if not initial_channel:
			initial_channel = ctx.channel

		if ctx.author not in initial_channel.members:
			await ctx.send(embed=self.bot.error("You don't have access to that channel"))
			return

		if rift_name in self.rift_name_cache:
			await ctx.send(embed=self.bot.error("There is already a rift with this name in use"))
			return

		rift_owner = ctx.author.id
		initial_channel = initial_channel.id

		owners_rifts = len([rift for rift in self.rift_name_cache.items() if rift["owner"] == rift_owner])
		if owners_rifts > 2:
			await ctx.send(embed=self.bot.error("You have too many rifts. The maximum is 3. Please contact the support server to request more"))
			return



		query = "INSERT INTO rift (rift_name, owner, channels) VALUES ($1, $2, $3)"
		await self.bot.pool.execute(query, rift_name, rift_owner, [initial_channel])

		self.rift_name_cache[rift_name] = {"owner" : rift_owner, "channels" : [initial_channel]}

	@checks.is_admin()
	@commands.command()
	async def join_rift(self, ctx, rift_name, channel: TextChannel = None):
		if not channel:
			channel = ctx.channel

		if ctx.author not in channel.members:
			await ctx.send(embed=self.bot.error("You don't have access to that channel"))
			return

		if rift_name not in self.rift_name_cache:
			await ctx.send(embed=self.bot.error("This is not a rift"))
			return

		owner = self.rift_name_cache[rift_name]["owner"]

		if ctx.author.id != owner:
			owner_user = self.bot.get_user(owner)
			if not owner_user:
				await ctx.send(embed=self.bot.error("The owner of this rift no longer has a connection with yori"))
				return

			message = await owner_user.send(embed=self.bot.notice(f"A request to add {channel.mention} to {rift_name} has been made by {ctx.author.mention}. React with ✔ or ✗ to confirm or deny"))
			await message.add_reaction("✔")
			await message.add_reaction("✗")
			await ctx.send(embed=self.bot.notice("A message has been sent to the owner of this rift for approval"))

			def check(reaction, user):
				if reaction.emoji not in ["✔","✗"]:
					return False
				if reaction.message.id != message.id:
					return False
				return True

			reaction, user = await self.bot.bot.wait_for("reaction_add", check=check)

			if reaction.emoji == "✗":
				return

		self.rift_name_cache[rift_name]["channels"].append(channel.id)
		query = "UPDATE rift SET channels = $1 where rift_name = $2"
		await self.bot.pool.execute(query, self.rift_name_cache[rift_name]["channels"], rift_name)
		await channel.send(self.bot.success(f"This channel is now connected to {rift_name}"))

	async def on_message(self, message):
		if message.channel.id not in self.rift_channel_cache:
			return

		connected_rifts = self.rift_channel_cache.get(message.channe.id)
		if not connected_rifts:
			return

		for rift in connected_rifts:
			channels = self.rift_name_cache[rift]["channels"]
			for channel in channels:
				actual_channel = self.bot.get_channel(channel)
				await actual_channel.send(embed=self.formatembed(message))

	async def update_descriptions(self):
		await self.bot.wait_until_ready

		for rift in self.rift_name_cache:
			channels_desc = []
			actual_channels = []
			for channel in rift["channels"]:
				actual_channel = self.bot.get_channel(channel)
				if actual_channel:
					actual_channel.append(actual_channel)
					channels_desc.append(f"{actual_channel.name} in {actual_channel.aguild}")
			for channel in actual_channels:
				await channel.edit(topic=" || ".join(channels_desc))













