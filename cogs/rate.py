import discord
from discord.ext import commands
import datetime
import random


class Rate:
    """Rate a user."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def rate(self, ctx):
        """Rates users. 157% accurate!"""

        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 10)
        y = ":sparkles:" *  x
        await ctx.send("{} gets a solid ** {}/10 ** \n {}".format(ctx.message.mentions[0].name, x, y))


def setup(bot):
    bot.add_cog(Rate(bot))