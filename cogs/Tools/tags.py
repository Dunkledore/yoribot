from discord.ext import commands
from discord import Embed, File
import asyncpg
import random
from ..utils import checks
import os


class Tags:

	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=["tag_add",'addtag','tagadd'])
	async def add_tag(self, ctx, tag_name, *, tag_content = None):
		if not ctx.message.attachemnets:
			file_name = None
		else:
			file = ctx.message.attachemnets[0]
			file_name = file.filename
			file_name_in_use = True
			while file_name_in_use:
				query = "SELECT file_name FROM tag WHERE file_name = $1"
				file = await self.bot.pool.fetch(query, file_name)
				if file:
					file_name = file_name + str(random.randint(10))
				else:
					file_name_in_use = False
					await file.save(f"../tag_files/{file_name}")

		query = "INSERT INTO tags (guild_id, tag_name, tag_content, file_name) VALUES ($1,$2,$3,$4)"
		try:
			await self.bot.pool.exexute(query, ctx.guild.id, tag_name, tag_content or "", file_name or "")
		except asyncpg.UniqueViolationError:
			await ctx.send(embed=self.bot.error("The tag is already in use in your guild. Pick another name"))

	@commands.command(aliases=["tag_remove","tagremove","removetag","tagdelete","deletetag","deltag","tagdel"])
	@checks.is_mod()
	async def remove_tag(self, ctx, tag_name):
		query = "DELETE FROM tags WHERE (guild_id = $1) and (tag_name = $2)"
		file_name = await self.bot.pool.fetchval(query, ctx.guild.id, tag_name)
		if file_name:
			os.remove(f"../tag_files/{file_name}")
		await ctx.send(embed=self.bot.succes(f"Removed {tag_name}"))

	@commands.command(aliases=["view_tag", "tag_list","list_tag","taglist"])
	async def tags(self, ctx):
		query = "SELECT tag_name FROM tags WHERE guild_id = $1"
		tags = await self.bot.pool.fetch(query, ctx.guild.id)
		await ctx.send(embed=Embed(title=f"Tags for {ctx.guild.name}", description="\n".join([tag['tag_name'] for tag in tags])))

	async def on_message(self, message):
		if message.author.bot:
			return
		if not message.guild:
			return

		ctx = await self.bot.get_context(message)
		if not ctx.prefix:
			return

		try:
			tag_name = message.content.replace(ctx.prefix, "", 1).split()[0]
			if not tag_name:
				return
		except IndexError:
			return

		query = "SELECT * FROM tags WHERE (guild_id = $1) and (tag_name = $2)"
		tag = await self.bot.fetchrow(query, message.guild.id, tag_name)
		if not tag:
			return

		await ctx.send(tag_name or None, file=File(f"../tag_files/{file_name}"))


def setup(bot):
	bot.add_cog(Tags(bot))


