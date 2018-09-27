from discord.ext import commands
import aiohttp
from discord import Embed


class Searches:
	"""Search different providers for information. (Google, Ubran Dictionary"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=["ubrandictionary", "ud"])
	async def urban(self, ctx, *, word):
		async with aiohttp.ClientSession() as cs:
			payload = {'term': word}
			url = "http://api.urbandictionary.com/v0/define"
			async with cs.get(url, params=payload) as r:
				data = await r.json()
				data = data["list"]
				if not data:
					await ctx.send(embed=self.bot.error("Word not found"))
					return
				url = f"http://{word}.urbanup.com"
				author = data[0]["author"]
				definition = data[0]["definition"]
				embed = Embed(title=f"{word.title()} by {author.title()}", description=definition, url=url)
				embed.set_footer(text="Powered By UrbanDictionary", icon_url="https://d2gatte9o95jao.cloudfront.net/assets/logo-1b439b7fa6572b659fbef161d8946372f472ef8e7169db1e47d21c91b410b918.svg")
				await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(Searches(bot))
