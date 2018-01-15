"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import discord
from discord.ext import commands
from .utils import checks
from cogs.utils.dataIO import dataIO
import os
import re
import asyncio


class Antilink:
    """Hate when people spam invite links to other Discord servers? This plugin allows you to prevent users from sharing links in chat and will notify the server owner when someone attempts to share a link.'"""

    __author__ = "Kowlin"
    __version__ = "AL-v1.1-LTS"

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/antilink/settings.json'
        self.json = dataIO.load_json(self.location)
        self.regex = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.gg|discordapp\.com\/invite)\b([-a-zA-Z0-9/]*)>?")
        self.regex_discordme = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.me\/)\b([-a-zA-Z0-9/]*)>?")


    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def antilinkownerdm(self, ctx):
        """Enable or disable notifications to the server owner via DM when a link is shared in the server."""
        serverid = ctx.message.guild.id
        if self.json[str(serverid)]['ownerdm'] is True:
            self.json[str(serverid)]['ownerdm'] = False
            await ctx.send('Owner DM now disabled')
        elif self.json[str(serverid)]['ownerdm'] is False:
            self.json[str(serverid)]['ownerdm'] = True
            await ctx.send('Owner DM now enabled')
        dataIO.save_json(self.location, self.json)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def toggleantilink(self, ctx):
        """Enable or disable anti-link entirely (if disabled, members can share links to other Discord servers)."""
        serverid = ctx.message.guild.id
        if self.json[str(serverid)]['toggle'] is True:
            self.json[str(serverid)]['toggle'] = False
            await ctx.send('Antilink is now disabled')
        elif self.json[str(serverid)]['toggle'] is False:
            self.json[str(serverid)]['toggle'] = True
            await ctx.send('Antilink is now enabled')
        dataIO.save_json(self.location, self.json)

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def antilinkmessage(self, ctx, *, text):
        """Customize the message sent to the person attempting to share a Discord link in your server."""
        serverid = ctx.message.guild.id
        self.json[str(serverid)]['message'] = text
        dataIO.save_json(self.location, self.json)
        await ctx.send('Message is set')
        if self.json[str(serverid)]['dm'] is False:
            await ctx.send('Remember: Direct Messages on removal is disabled!\nEnable it with ``antilinktoggledm``')

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def antilinktoggledm(self, ctx):
        """ Enable or Disable the anti-link DM"""
        serverid = ctx.message.guild.id
        if self.json[str(serverid)]['dm'] is False:
            self.json[str(serverid)]['dm'] = True
            await ctx.send('Enabled DMs on removal of invite links')
        elif self.json[str(serverid)]['dm'] is True:
            self.json[str(serverid)]['dm'] = False
            await ctx.send('Disabled DMs on removal of invite links')
        dataIO.save_json(self.location, self.json)

    async def _new_message(self, message):
        """Finds the message and checks it for regex"""
        user = message.author
        if message.guild is None:
            return
        if str(message.guild.id) in self.json:
            if self.json[str(message.guild.id)]['toggle'] is True:
                if self.regex.search(message.content) is not None or self.regex_discordme.search(message.content) is not None:
                    roles = [r.name for r in user.roles]
                    #bot_admin = settings.get_server_admin(message.server) add these one day
                    #bot_mod = settings.get_server_mod(message.server)
                    if user.id == message.guild.owner.id:
                        return
                    #elif bot_admin in roles:
                    #    return
                    #elif bot_mod in roles:
                    #    return
                    #elif user.permissions_in(message.channel).manage_messages is True:
                    #    return
                    else:
                        asyncio.sleep(0.5)
                        await message.delete()
                        if (self.json[str(message.guild.id)]['dm'] is True) and (self.json[str(message.guild.id)]['message'] != ""):
                            if message.author.dm_channel is None:
                                await message.author.create_dm()
                            await message.author.dm_channel.send(self.json[str(message.guild.id)]['message'])
                        if self.json[str(message.guild.id)]['ownerdm'] is True:
                            if message.guild.owner.dm_channel is None:
                                await message.guild.owner.create_dm()
                            await message.guild.owner.dm_channel.send(message.author.mention + " posted " + message.content + " in " + message.channel.name)

def check_folder():
    if not os.path.exists('data/antilink'):
        os.makedirs('data/antilink')


def check_file():
    f = 'data/antilink/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = Antilink(bot)
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')
