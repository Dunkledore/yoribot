import discord
from discord.ext import commands
import random


class Rate:
    """Rate a user."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def rate(self, ctx):
        """Rates users. 157% accurate!"""

        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.timestamp.timestamp()),)
        x = ":sparkles:" * random.randint(1, 10)
        ctx.send("{} gets a solid: ".format(user.name) + x)


def setup(bot):
    bot.add_cog(Rate(bot))