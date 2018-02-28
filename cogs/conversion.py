import aiohttp
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from cogs.utils import checks
import re
import os
from .utils.dataIO import dataIO
import os.path
import math

import pytz  # pip install pytz



class Convert:
    """Currency converter"""

    def __init__(self, bot):
        self.bot = bot
        self.currencies = ['AUD', 'BGN', 'BRL', 'CAD', 'CHF', 'CNY', 'CZK', 'DKK', 'EUR', 'GBP', 'HKD', 'HRK', 'HUF', 'IDR', 'ILS', 'INR', 'JPY', 'KRW', 'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'RUB', 'SEK', 'SGD', 'THB', 'TRY', 'USD', 'ZAR']


    @commands.command()
    async def moneyconvert(self, ctx, amount: float, base: str, to: str):
        """Base is the money to convert from and to is the money to convert to. \nAvailable currencies for conversion: \nAUD BGN BRL CAD CHF CNY CZK DKK EUR GBP HKD HRK HUF IDR ILS INR JPY KRW MXN MYR NOK NZD PHP PLN RON RUB SEK SGD THB TRY USD ZAR"""
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


def setup(bot):

    bot.add_cog(Convert(bot))