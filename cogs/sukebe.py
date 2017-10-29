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
        await ctx.send(ctx.message.mentions[0].id)
        await ctx.send(ctx.message.mentions[0])
        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.timestamp.timestamp()),)
        x = ":sparkles:" * random.randint(1, 10)
        await ctx.send(x)
        await ctx.send("{} gets a solid: ".format(ctx.message.mentions[0]) + x)


def setup(bot):
    bot.add_cog(Rate(bot))