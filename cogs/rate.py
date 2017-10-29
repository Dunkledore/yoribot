import discord
from discord.ext import commands
import random


class Rate:
    """Rate a user."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def rate(self, ctx, *, mention):
        """Rates users. 157% accurate!"""
        author = ctx.message.author.id
        mentionlist = ctx.message.mentions
        user = mentionlist[0]
        random.seed(int(user.id) % int(ctx.message.timestamp.timestamp()),)
        x = ":sparkles:" * random.randint(1, 10)
        await ctx.send("{} gets a solid: ".format(user.name) + x)


def setup(bot):
    bot.add_cog(Rate(bot))