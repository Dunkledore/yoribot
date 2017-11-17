import discord
from discord.ext import commands
from .utils import checks

class Musichelp:
    """Use this to display the help info for the music plugin."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def musichelp(self, ctx):
        em = discord.Embed(color=ctx.message.author.color, description="The following commands can be used to control the music player:")
        em.set_author(name="About Yori Bot", icon_url="http://yoribot.com/wp-content/uploads/2017/11/yoriicon.png")
        em.add_field(name='play', value='Play a song or playlist from YouTube.', inline=False)
        em.add_field(name='playnext', value='Will play the indicated song next.', inline=False)
        em.add_field(name='playnow', value='Stops currently playing song to play another.', inline=False)
        em.set_image(url='https://i.gyazo.com/c7722437eb4f75a992b1871bae091230.gif')
        em.set_footer(text= "Use the help command or visit http://yoribot.com for more information.")
        await ctx.send(embed=em)

def setup(bot):
    n=Musichelp(bot)
    bot.add_cog(n)