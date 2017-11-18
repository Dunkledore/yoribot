from copy import deepcopy
import os
import os.path

import discord
from discord.ext import commands
from discord.utils import find

from .utils.dataIO import dataIO
from .utils import checks, chat_formatting as cf


default_settings = {
    "enabled": False,
    "role": None
}


class StreamRole:

    """Assign a configurable role to anyone who is streaming."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_path = "data/streamrole/settings.json"
        self.settings = dataIO.load_json(self.settings_path)

    @commands.group(pass_context=True, no_pm=True, name="streamroleset")
    @checks.admin_or_permissions(manage_guild=True)
    async def _streamroleset(self, ctx):
        """Sets StreamRole settings."""

        guild = ctx.message.guild
        if str(guild.id) not in self.settings:
            self.settings[str(guild.id)] = deepcopy(default_settings)
            dataIO.save_json(self.settings_path, self.settings)


    @_streamroleset.command(pass_context=True, no_pm=True, name="toggle")
    @checks.admin_or_permissions(manage_guild=True)
    async def _toggle(self, ctx):
        """Toggles StreamRole on/off."""

        await ctx.message.channel.trigger_typing()

        guild = ctx.message.guild
        if (not self.settings[guild.id]["enabled"] and
                self.settings[guild.id]["role"] is None):
            await ctx.send(cf.warning(
                "You need to set the role before turning on StreamRole."
                " Use `{}streamroleset role`".format(ctx.prefix)))
            return

        self.settings[guild.id][
            "enabled"] = not self.settings[guild.id]["enabled"]
        if self.settings[guild.id]["enabled"]:
            await ctx.send(
                cf.info("StreamRole is now enabled."))
        else:
            await ctx.send(
                cf.info("StreamRole is now disabled."))
        dataIO.save_json(self.settings_path, self.settings)

    @_streamroleset.command(pass_context=True, no_pm=True, name="role")
    @checks.admin_or_permissions(manage_guild=True)
    async def _role(self, ctx, role: discord.Role):
        """Sets the role that StreamRole assigns to
        members that are streaming.
        """

        await ctx.message.channel.trigger_typing()

        guild = ctx.message.guild
        self.settings[str(guild.id)]["role"] = str(role.id)
        dataIO.save_json(self.settings_path, self.settings)

        await ctx.send(
            cf.info("Any member who is streaming will now be given the "
                    "role `{}`. Ensure you also toggle the cog on with "
                    "`{}streamroleset toggle`.".format(role.name, ctx.prefix)))

    async def stream_listener(self, before: discord.Member,
                              after: discord.Member):
        if str(before.guild.id) not in self.settings:
            self.settings[str(before.guild.id)] = deepcopy(default_settings)
            dataIO.save_json(self.settings_path, self.settings)

        guild_settings = self.settings[str(before.guild.id)]
        if guild_settings["enabled"] and guild_settings["role"] is not None:
            streamer_role = find(lambda m: (str(m.id) == guild_settings["role"],
                                 before.guild.roles)
            if streamer_role is None:
                return
            # is streaming
            if (after.game is not None and
                    after.game.type == 1 and
                    streamer_role not in after.roles):
                await self.bot.add_roles(after, streamer_role)
            # is not
            elif ((after.game is None or after.game.type != 1) and
                  streamer_role in after.roles):
                await self.bot.remove_roles(after, streamer_role)


def check_folders():
    if not os.path.exists("data/streamrole"):
        print("Creating data/streamrole directory...")
        os.makedirs("data/streamrole")


def check_files():
    f = "data/streamrole/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/streamrole/settings.json...")
        dataIO.save_json(f, {})


def setup(bot: commands.Bot):
    check_folders()
    check_files()
    n = StreamRole(bot)
    bot.add_listener(n.stream_listener, "on_member_update")

    bot.add_cog(n)
