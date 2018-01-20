import aiohttp
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from cogs.utils import checks
import re
import os
from .utils.dataIO import dataIO
import pycountry
import pytz
from pytz import country_timezones
import googlemaps as googlemaps
from .utils import checks


#MUST LOAD THESE PYTHON PACKAGES OR THIS WILL NOT WORK pytz, pycountry, googlemaps

class Convert:
    """Currency converter"""

    def __init__(self, bot):
        self.bot = bot
        self.currencies = ['AUD', 'BGN', 'BRL', 'CAD', 'CHF', 'CNY', 'CZK', 'DKK', 'EUR', 'GBP', 'HKD', 'HRK', 'HUF', 'IDR', 'ILS', 'INR', 'JPY', 'KRW', 'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'RUB', 'SEK', 'SGD', 'THB', 'TRY', 'USD', 'ZAR']
        self.countries = dataIO.load_json("data/countrycode/countries.json")
        self.subregions = dataIO.load_json("data/countrycode/subregions.json")
        self.settings = dataIO.load_json("data/countrycode/settings.json")
        self.utc = pytz.utc

    @commands.command()
    async def moneyconvert(self, ctx, amount: float, base: str, to: str):
        """Currency converter
        Set the amount, currency FROM (base) and currency TO 
        Available currencies for conversion:
        AUD BGN BRL CAD CHF CNY CZK DKK EUR GBP HKD HRK HUF IDR ILS INR JPY KRW MXN MYR NOK NZD PHP PLN RON RUB SEK SGD THB TRY USD ZAR
        ***WARNING***
        Conversion may not be exact"""
        if base.upper() not in self.currencies or to.upper() not in self.currencies:
            await ctx.send('One or both of the currencies selected are invalid')
        else:
            api = 'http://api.fixer.io/latest?base={}'.format(base.upper())
            async with aiohttp.request("GET", api) as r:
                result = await r.json()
                rate = result['rates'][to.upper()]
                converted_amount = amount * rate
                pre_conv = '{0:.2f}'.format(amount)
                post_conv = '{0:.2f}'.format(converted_amount)
                em = discord.Embed(color=ctx.message.author.color, description=" ")
                em.set_author(name="Currency Conversion", icon_url="http://bit.ly/2BfWPuR")
                em.add_field(name='{}'.format(base.upper()), value='{}'.format(pre_conv))
                em.add_field(name='{}'.format(to.upper()), value='{}'.format(post_conv))
                em.set_footer(text= "Currency exchange rates based on http://fixer.io")
                await ctx.send(embed=em)
    async def timecheck(self, ctx, code: str):
        try:
            if (self.settings["gmaps"] is None) | (self.settings["gmaps"]["key"] is None):
                await ctx.send("GMaps Timezone API is not set up. Please head to <https://developers.google.com/maps/documentation/timezone/intro> and get your api key!")
                return
        except KeyError:
            await ctx.send("GMaps Timezone API is not set up. Please head to <https://developers.google.com/maps/documentation/timezone/intro> and get your api key!")
            return
        self.gmaps = googlemaps.Client(key=self.settings["gmaps"]["key"])
        fmt = '%H:%M'
        geocode_result = self.gmaps.geocode(code)
        timezone_result = self.gmaps.timezone(geocode_result[0]['geometry']['location'])
        local = pytz.timezone(timezone_result['timeZoneId'])
        utc_dt = datetime.now(tz=self.utc)
        time = utc_dt.astimezone(local)
        await ctx.send(
            "Its currently " + time.strftime(fmt) + " in " + geocode_result[0]['formatted_address'] + "!")
            
    @commands.group(pass_context=True, no_pm=True)
    @checks.is_admin()
    async def timezone_settings(self, ctx):
        """Manages settings for the timezone cog."""
        if ctx.invoked_subcommand is None:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='timezone_settings')
            
    @timezone_settings.command(name="gmaps", pass_context=True)
    async def _imgur(self, ctx, key:str):
        """Setting for gmaps api."""
        self.settings["gmaps"]={}
        self.settings["gmaps"]["key"]= key
        dataIO.save_json("data/countrycode/settings.json", self.settings)
        await ctx.send("gmaps set!")
        
    @commands.group(pass_context=True)
    async def timezone(self, ctx):
        """General time stuff."""
        if ctx.invoked_subcommand is None:
            help_cmd = self.bot.get_command('help')
            await ctx.invoke(help_cmd, command='timezone')

    @timezone.command(name="user",pass_context=True)
    async def time(self, ctx, user: discord.Member = None):
        """Example: [p]timezone to display your own timezone / [p]timezone <user> to display a users timezone"""
        author = ctx.message.author
        self.countries = dataIO.load_json("data/countrycode/countries.json")
        self.subregions = dataIO.load_json("data/countrycode/subregions.json")
        subregionobj = None
        countryobj = None
        if not user:
            user = author
        for subregion in self.subregions:
            if user.id in self.subregions[subregion]:
                try:
                    subregionobj = pycountry.subdivisions.get(code=subregion)
                    countryobj = subregionobj.country
                    break
                except:
                    subregionobj = None
                    continue
        if subregionobj is None:
            for country in self.countries:
                if user.id in self.countries[country]:
                    try:
                        countryobj = pycountry.countries.get(name=country)
                        break
                    except:
                        continue

        if countryobj is not None:
            if subregionobj is not None:
                await self.timecheck(subregionobj.code)
            else:
                await self.timecheck(countryobj.name)
        else:
            await ctx.send(
                "Sorry I don't know the country of the user! Is the country set in the profile?")
                
    @timezone.command(pass_context=True)
    async def location(self, ctx, location: str = ""):
        """Example: [p]localtime location <ISO Code>"""
        re1 = '((?:[a-z][a-z]+))'  # Word 1
        re2 = '.*?'  # Non-greedy match on filler
        re3 = '((?:[a-z][a-z]+))'  # Word 2
        rg = re.compile(re1 + re2 + re3, re.IGNORECASE | re.DOTALL)

        m = rg.search(location)
        subregionobj = None
        try:
            if m:
                word1 = m.group(1)
                countryobj = pycountry.countries.get(alpha_2=word1.upper())
                subregionobj = pycountry.subdivisions.get(code=location.upper())
            else:
                countryobj = pycountry.countries.get(alpha_2=location.upper())
        except:
            countryobj = None
        if countryobj is not None:
            if subregionobj is not None:
                await self.timecheck(subregionobj.code)
            else:
                await self.timecheck(countryobj.alpha_2)
        else:
            await ctx.send(
                "Sorry I don't know your country! Did you use the correct ISO countrycode? \nExample: `-localtime GB`\n`-localtime US-CA`")


def check_folders():
    folders = ("data", "data/countrycode/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)
            
def check_files():
    if not os.path.isfile("data/countrycode/countries.json"):
        print("Creating empty countries.json...")
        dataIO.save_json("data/countrycode/countries.json", {})
    if not os.path.isfile("data/countrycode/subregions.json"):
        print("Creating empty subregions.json...")
        dataIO.save_json("data/countrycode/subregions.json", {})

def setup(bot):
    bot.add_cog(Convert(bot))