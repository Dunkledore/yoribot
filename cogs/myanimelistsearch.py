import discord
from discord.ext import commands

class MyAnimeListSearch:
    """Commences a search on MyAnimeList"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def anime(self, ctx, *text):
        """Returns MAL anime search result using anime name"""

        #Your code will go here
        text = " ".join(text)
        query=text.replace(" ", "%20")
        await ctx.send("http://myanimelist.net/anime.php?q="+query)

    @commands.command()
    async def manga(self, ctx, text):
        """Returns MAL manga search result using manga name"""

        #Your code will go here
        query=text.replace(" ", "%20")
        await ctx.send("http://myanimelist.net/manga.php?q="+query)

    @commands.command()
    async def malcharacter(self, ctx, text):
        """Returns MAL character search result using char name"""

        #Your code will go here
        query=text.replace(" ", "%20")
        await ctx.send("http://myanimelist.net/character.php?q="+query)

    @commands.command()
    async def animelist(self, ctx, text):
        """Returns a user's MyAnimeList anime list"""

        #Your code will go here
        query=text
        await ctx.send("http://myanimelist.net/animelist/"+query)

    @commands.command()
    async def mangalist(self, ctx, text):
        """Returns a user's MyAnimeList manga list"""

        #Your code will go here
        query=text
        await ctx.send("http://myanimelist.net/mangalist/"+query)

    @commands.command()
    async def mal(self, ctx, text):
        """Returns MAL search result using search name"""

        #Your code will go here
        query=text.replace(" ", "%20")
        await ctx.send(" http://myanimelist.net/search/all?q="+query)

def setup(bot):
    bot.add_cog(MyAnimeListSearch(bot))
