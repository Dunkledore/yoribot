from discord.ext import commands
from PyDictionary import PyDictionary


class Dictionary:
	"""Search for definitions, synonyms and antonyms."""

	def __init__(self, bot):
		self.bot = bot
		self.dictionary = PyDictionary()

	@commands.command(name="define", pass_context=True)
	async def define(self, ctx, *, word: str):
		"""Displays definitions of a given word"""
		search_term = word.split(" ", 1)[0]
		result = self.dictionary.meaning(search_term)
		str_buffer = ""
		if result is None:
			await self.bot.delete_message(x)
			await ctx.send("This word is not in the dictionary.")
			return
		for key in result:
			str_buffer += "\n**" + key + "**: \n"
			counter = 1
			j = False
			for val in result[key]:
				if val.startswith("("):
					str_buffer += str(counter) + ". *" + val + ")* "
					counter += 1
					j = True
				else:
					if j:
						str_buffer += val + "\n"
						j = False
					else:
						str_buffer += str(counter) + ". " + val + "\n"
						counter += 1
		await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                description = str_buffer))

	@commands.command(name="antonym", pass_context=True)
	async def antonym(self, ctx, *, word: str):
		"""Displays antonyms for a given word"""
		search_term = word.split(" ", 1)[0]
		result = self.dictionary.antonym(search_term)
		if result is None:
			await self.bot.delete_message(x)
			await ctx.send("This word is not in the dictionary.")
			return
		await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                description ="Antonyms for **" + search_term + "**: *" + "*, *".join(result) + "*"))

	@commands.command(name="synonym", pass_context=True)
	async def synonym(self, ctx, *, word: str):
		"""Displays synonyms for a given word"""
		search_term = word.split(" ", 1)[0]
		result = self.dictionary.synonym(search_term)
		if result is None:
			await self.bot.delete_message(x)
			await ctx.send("This word is not in the dictionary.")
			return
		await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                description ="Synonyms for **" + search_term + "**: *" + "*, *".join(result) + "*"))


def setup(bot):
	bot.add_cog(Dictionary(bot))