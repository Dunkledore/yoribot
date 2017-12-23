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
    @checks.is_mod()
    async def qembed(self, ctx, channel: discord.TextChannel, title, *, description):
        """A Quck way to send an embed to a channel"""

        embed = discord.Embed(title=title, description=description)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await channel.send(embed=embed)


    @commands.command(no_pm=True)
    @checks.is_mod()
    async def embed(self, ctx, channel: discord.TextChannel):
        """A Lengthy way to send a detailed embed to a channel"""


        def check(m):
            if m.author != ctx.message.author:
                return False
            if m.channel != ctx.message.channel:
                return False
            return True
        
        messages_to_delete = [ctx.message]
        
        #Ttile
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

        #Description
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

        #Url
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

        #fields
        more_fields = True
        fields = []
        while(more_fields):
            bot_message = await ctx.send("Please type the field title or \"none\" to stop adding fields")
            messages_to_delete.append(bot_message)
            field_title_message = await self.bot.wait_for('message', timeout=30.0, check=check)
            messages_to_delete.append(field_title_message)
            field_title = field_title_message.content
            while len(field_title) > 256:
                bot_message = await ctx.send("Character limit of 256 please enter less now")
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
                while len(field_content) > 1024:
                    bot_message = await ctx.send("Character limit of 1024 please enter less now")
                    messages_to_delete.append(bot_message)
                    field_content_message = await self.bot.wait_for('message', timeout=30.0, check=check)
                    messages_to_delete.append(field_content_message)
                    field_content = field_content_message.content

                fields.append([field_title, field_content])

        for field in fields:
            embed.add_field(name=field[0], value=field[1])

        #Add Footer
        bot_message = await ctx.send("Please type the embed footer or \"none\" for no footer")
        messages_to_delete.append(bot_message)
        footer_message = await self.bot.wait_for('message', timeout=30.0, check=check)
        messages_to_delete.append(footer_message)
        footer = footer_message.content
        if footer not in ["None", "none", "\"none\"", "\"None\""]:
            embed.set_footer(text=footer)


        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        await channel.send(embed=embed)

        # Add to delete messages after
        #for message in messages_to_delete:
        #   await message.delete()
                        




def setup(bot):
    bot.add_cog(Embed(bot))




