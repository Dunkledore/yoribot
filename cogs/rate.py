import discord
from discord.ext import commands
import datetime
import random
try:
    from bs4 import BeautifulSoup
    soupAvailable = True
except:
    soupAvailable = False
import aiohttp

class Ratings:
    """Have the bot rate things about users."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def sparkles(self, ctx):
        """Rates users sparkliness. 157% accurate!"""

        random.seed(int(ctx.message.mentions[0].id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 10)
        y = ":sparkles:" *  x
        await ctx.send("{} gets a solid ** {}/10 ** \n {}".format(ctx.message.mentions[0].name, x, y))
    
    @commands.command(aliases=['lovecalc'])
    async def ship(self, ctx, lover: discord.Member, loved: discord.Member):
        """Calculate their love!"""

        x = lover.display_name
        y = loved.display_name

        url = 'https://www.lovecalculator.com/love.php?name1={}&name2={}'.format(x.replace(" ", "+"), y.replace(" ", "+"))
        async with aiohttp.get(url) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
            try:
                description = soupObject.find('div', attrs={'class': 'result score'}).get_text().strip()
            except:
                description = 'Dr. Love is busy right now'

        try:
            z = description[:2]
            z = int(z)
            if z > 50:
                emoji = '❤'
            else:
                emoji = '💔'
            title = 'Dr. Love says that the love percentage for {} and {} is:'.format(x, y)
        except:
            emoji = ''
            title = 'Dr. Love has left a note for you.'
            
        description = emoji + ' ' + description + ' ' + emoji
        em = discord.Embed(title=title, description=description, color=discord.Color.red())
        await ctx.send(embed=em)

def setup(bot):
    if soupAvailable:
        bot.add_cog(Ratings(bot))
    else:
        raise RuntimeError("You need to run `pip3 install beautifulsoup4`")