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
        em.set_author(name="Advanced Music Player Help", icon_url="http://yoribot.com/wp-content/uploads/2017/11/yoriicon.png")
        em.add_field(name='play', value='Play a song or playlist from YouTube.', inline=False)
        em.add_field(name='playnext', value='Will play the indicated song next.', inline=False)
        em.add_field(name='playnow', value='Stops currently playing song to play another.', inline=False)
        em.add_field(name='pause, resume', value='Will pause and resume playback.', inline=False)
        em.add_field(name='shuffle', value='Shuffles the list of songs queued.', inline=False)
        em.add_field(name='stop', value='Stops the music from playing.', inline=False)
        em.add_field(name='front', value='Moves the player window to the front of the chat.', inline=False)
        em.set_image(url='https://i.gyazo.com/476ca3539836bfd7e5240f1f5366fa80.gif')
        em.set_footer(text= "Use the help command or visit http://yoribot.com for more information.")
        await ctx.send(embed=em)

def setup(bot):
    n=Musichelp(bot)
    bot.add_cog(n)