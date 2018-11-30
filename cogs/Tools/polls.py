from discord.ext import commands
from discord import Embed, Forbidden, HTTPException
import asyncio

def to_emoji(c):
    base = 0x1f1e6
    return chr(base + c)

class Polls:
    """Poll voting system."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def poll(self, ctx, *, question):
        """Interactively creates a poll with the following question.
        To vote, use reactions!
        """

        # a list of messages to delete when we're all done
        to_delete = [ctx.message]
        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) <= 100

        for i in range(20):
            to_delete.append(await ctx.send(f"Say poll option or {ctx.prefix}cancel to publish poll."))

            try:
                entry = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                break

            to_delete.append(entry)

            if entry.content.startswith ==f"{ctx.prefix}cancel":
                break

            answers.append(entry.clean_content)

        try:
            await ctx.channel.delete_messages(to_delete)
        except (Forbidden, HTTPException):
            pass


        embed = Embed(title=question, description="\n".join(f"{counter}\U000020e3 : {answer}" for counter, answer in enumerate(answers)))
        embed.set_author(name=ctx.author.name,icon_url=ctx.author.avatar_url)
        poll_message = await ctx.send(embed=embed)
        for counter, answer in enumerate(answers):
            await poll_message.add_reaction(str(counter)+"\U000020e3")

def setup(bot):
    bot.add_cog(Polls(bot))