from .utils import db, checks, formats, cache
from .utils.paginator import Pages
from pint import UnitRegistry

from discord.ext import commands

import discord
import asyncio


class Conversion:
    """Commands used to send embeds"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def convert(self, ctx, *, conversion_string):
       	
       	#pass conversion string
       	stringarr = conversion_string.split()
       	if stringarr[2] = 'to':
       		del stringarr[2]

       	first_quantity = stringarr[0]
       	first_unit = stringarr[1]
       	second_unit = stringarr[2]

       	ureg = UnitRegistry()

       	first_value = first_quantity * ureg.parse_expression(first_unit)
       	second_value = first_value.to(ureg.parse_expression(second_unit))

       	await ctx.send(second_value)




   


def setup(bot):
    bot.add_cog(Conversion(bot))




