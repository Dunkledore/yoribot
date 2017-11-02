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
    """Blocks Discord invite links from users who don't have the permission 'Manage Messages'"""

    __author__ = "Kowlin"
    __version__ = "AL-v1.1-LTS"

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/antilink/settings.json'
        self.json = dataIO.load_json(self.location)
        self.regex = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.gg|discordapp\.com\/invite)\b([-a-zA-Z0-9/]*)>?")
        self.regex_discordme = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.me\/)\b([-a-zA-Z0-9/]*)>?")

    @commands.group(pass_context=True, no_pm=True)
    async def antilinkset(self, ctx):
        """Manages the settings for antilink."""
        serverid = ctx.message.guild.id
        #if ctx.invoked_subcommand is None:
            #await send_cmd_help(ctx)
        if str(serverid) not in self.json:
            self.json[str(serverid)] = {'toggle': False, 'message': '', 'dm': False}

    @antilinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggle(self, ctx):
        """Enable/disables antilink in the server"""
        serverid = ctx.message.guild.id
        if self.json[str(serverid)]['toggle'] is True:
            self.json[str(serverid)]['toggle'] = False
            await ctx.send('Antilink is now disabled')
        elif self.json[str(serverid)]['toggle'] is False:
            self.json[str(serverid)]['toggle'] = True
            await ctx.send('Antilink is now enabled')
        dataIO.save_json(self.location, self.json)

    @antilinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def message(self, ctx, *, text):
        """Set the message for when the user sends a illegal discord link"""
        serverid = ctx.message.guild.id
        self.json[str(serverid)]['message'] = text
        dataIO.save_json(self.location, self.json)
        await ctx.send('Message is set')
        if self.json[str(serverid)]['dm'] is False:
            await ctx.send('Remember: Direct Messages on removal is disabled!\nEnable it with ``antilinkset toggledm``')

    @antilinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggledm(self, ctx):
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
                    if user.id == guild.owner.id:
                        return
                    #elif bot_admin in roles:
                    #    return
                    #elif bot_mod in roles:
                    #    return
                    #elif user.permissions_in(message.channel).manage_messages is True:
                    #    return
                    else:
                        asyncio.sleep(0.5)
                        await self.bot.delete_message(message)
                        if self.json[str(message.server.id)]['dm'] is True:
                            await ctx.send(message.author, self.json[str(message.guild.id)]['message'])


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
