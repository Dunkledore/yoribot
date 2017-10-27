import asyncio
import json

import aiohttp
from discord.ext import commands

class CatsandDogsImages:
    """Gets random pictures of cats or dogs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.url_dog = "https://random.dog/woof.json"
        self.url_cat = "https://random.cat/meow"

    @commands.command(pass_context=True, no_pm=True)
    async def meow(self, ctx: commands.Context):
        """Gets a random cat picture."""

        async with aiohttp.get(self.url_cat) as response:
            img = json.loads(await response.text())["file"].replace("\\/","/")
            await self.bot.say(img)

    @commands.command(pass_context=True, no_pm=True)
    async def woof(self, ctx: commands.Context):
        """Gets a random dog picture."""

        async with aiohttp.get(self.url_dog) as response:
            img = json.loads(await response.text())["url"]
            await self.bot.say(img)

def setup(bot: commands.Bot):
    bot.add_cog(CatsandDogsImages(bot))
