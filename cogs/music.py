from discord.ext import commands
from .utils import checks, formats
from .utils.paginator import HelpPaginator, CannotPaginate
import discord

class MusicHelp:
    """Use this to display the help info for the music plugin."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def musichelp(self, ctx):
        """Displays my intro message."""
        em = discord.Embed(color=ctx.message.author.color, description="Yori is a premium Discord bot based on the rapptz robodanny code and heavily customized with influences also from Red-DiscordBot.")
        em.set_author(name="About Yori Bot", icon_url="http://yoribot.com/wp-content/uploads/2017/11/yoriicon.png")
        em.set_image(url='https://i.gyazo.com/c7722437eb4f75a992b1871bae091230.gif')
        em.set_footer(text= "Use the help command or visit http://yoribot.com for more information.")
        await ctx.send(embed=em)

def setup(bot):
    n=MusicHelp(bot)
    bot.add_cog(n)