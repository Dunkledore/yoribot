from .utils import db, checks, formats, cache
from .utils.paginator import Pages

from discord.ext import commands
import json
import re
import datetime
import discord
import asyncio
import traceback
import asyncpg
import psutil

class Embed:
    """Commands used to set up your server profile"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(no_pm=True)
    async def embed(self, ctx, channel: discord.TextChannel):


        def check(m):
            if m.author != ctx.message.author:
                return False
            if m.channel != ctx.message.channel:
                return False
            return True
        
        messages_to_delete = []
        
        bot_message = await ctx.send("Please type the embed title")
        messages_to_delete.append(bot_message)
        title_message = await self.bot.wait_for('message', timeout=30.0, check=check)
        messages_to_delete.append(title_message)
        title = title_message.content
        while len(title) > 256:
            bot_message = await ctx.send("Character limit of 256 please enter less now")
            title_message = await self.bot.wait_for('message', timeout)
            messages_to_delete.append(title_message)
            title = title_message.content


        bot_message = await ctx.send("Please type the embed description")
        messages_to_delete.append(bot_message)
        description_message = await self.bot.wait_for('message', timeout=30.0, check=check)
        messages_to_delete.append(description_message)
        description = description_message.content
        while len(description) > 2048:
            await ctx.send("Character limit of 2048 please enter less now")
            description_message = await self.bot.wait_for('message', timeout)
            messages_to_delete.append(description_message)
            description = description_message.content

        
        bot_message = await ctx.send("Please type the embed url or \"none\" for no url")
        messages_to_delete.append(bot_message)
        url_message = await self.bot.wait_for('message', timeout=30.0, check=check)
        messages_to_delete.append(url_message)
        url = url_message.content
        if url not in ["None", "none", "\"none\"", "\"None\""]:
            embed = discord.Embed(title=title, description=description, url=url)
        else:
            embed = discord.Embed(title=title, description=description)

        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)


        more_fields = True
        fields = []
        while(more_fields):
            bot_message = await ctx.send("Please type the field title or \"none\" to stop adding fields")
            messages_to_delete.append(bot_message)
            field_title_message = await self.bot.wait_for('message', timeout=30.0, check=check)
            messages_to_delete.append(field_title_message)
            field_title = field_title_message.content
            if field_title in ["None", "none", "\"none\"", "\"None\""]:
                more_fields = False
            else:
                bot_message = await ctx.send("Please type the field content")
                messages_to_delete.append(bot_message)
                field_content_message = await self.bot.wait_for('message', timeout=30.0, check=check)
                field_content = field_content_message.content
                messages_to_delete.append(field_content_message)
                fields.append([field_title, field_content])

        for field in fields:
            embed.add_field(name=field[0], value=field[1])

        await channel.send(embed=embed)

        for message in messages_to_delete:
            await message.delete()
                      





     








def setup(bot):
    bot.add_cog(Embed(bot))




