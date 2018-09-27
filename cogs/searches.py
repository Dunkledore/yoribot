from discord.ext import commands
import aiohttp
from discord import Embed
import asyncio


class Searches:
	"""Search different providers for information. (Google, Urban Dictionary...)"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases=["ubrandictionary", "ud"])
	async def urban(self, ctx, *, word):
		"""Search urban dictionary"""
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
				embed.set_footer(text="Powered By UrbanDictionary", icon_url="https://img.lgbtdis.co/images/2018/09/27/58a9c165e53c370ac4be52a7a98c35c3.md.png")
				await ctx.send(embed=embed)

	@commands.command()
	async def dadjoke(self, ctx):
		"""See a dadjoke"""
		def make_embed(text):
			embed = Embed(title="DadJoke", description=text)
			embed.set_footer(text="Dad Joke provide by https://icanhazdadjoke.com")
			return embed
		async with aiohttp.ClientSession() as cs:
			url = 'https://icanhazdadjoke.com/'
			headers = {'Accept': 'text/plain'}
			async with cs.get(url, headers=headers) as r:
				joke = await r.text()
				head, sep, tail = joke.partition('?' or '.')
				await ctx.send(embed=make_embed(head))
				if tail:
					asyncio.sleep(5)
					await ctx.send(embed=make_embed(tail))

def setup(bot):
	bot.add_cog(Searches(bot))
