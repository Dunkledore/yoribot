# Cookie was created by Redjumpman for Redbot
# Design credit to discord user Yukirin for commissioning this project

# Standard Library
import asyncio
import os
import random
import time
from operator import itemgetter

# Discord and Red
import discord
from .utils import checks
from .utils.dataIO import dataIO
from discord.ext import commands


class PluralDict(dict):
    """This class is used to plural strings

    You can plural strings based on the value input when using this class as a dictionary.
    """
    def __missing__(self, key):
        if '(' in key and key.endswith(')'):
            key, rest = key.split('(', 1)
            value = super().__getitem__(key)
            suffix = rest.rstrip(')').split(',')
            if len(suffix) == 1:
                suffix.insert(0, '')
            return suffix[0] if value <= 1 else suffix[1]
        raise KeyError(key)


class Cookie:
    """Yori loves cookies, and will steal from others for you!"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/cookie/cookie.json"
        self.system = dataIO.load_json(self.file_path)

    @commands.group(pass_context=True, no_pm=True)
    async def setcookie(self, ctx):
        """Cookie settings group command"""

    @setcookie.command(name="stealcd", pass_context=True, hidden=True)
    @checks.admin_or_permissions(manage_guild=True)
    async def _stealcd_heist(self, ctx, cooldown: int):
        """Set the cooldown for stealing cookies"""
        guild = ctx.message.guild
        settings = self.check_guild_settings(guild)
        if cooldown >= 0:
            settings["Config"]["Steal CD"] = cooldown
            dataIO.save_json(self.file_path, self.system)
            msg = "Cooldown for steal set to {}".format(cooldown)
        else:
            msg = "Cooldown needs to be higher than 0."
        await ctx.send(msg)

    @setcookie.command(name="cookiecd", pass_context=True)
    @checks.admin_or_permissions(manage_guild=True)
    async def _cookiecd_heist(self, ctx, cooldown: int):
        """Set the cooldown for cookie command"""
        guild = ctx.message.guild
        settings = self.check_guild_settings(guild)
        if cooldown >= 0:
            settings["Config"]["Cookie CD"] = cooldown
            dataIO.save_json(self.file_path, self.system)
            msg = "Cooldown for cookie set to {}".format(cooldown)
        else:
            msg = "Cooldown needs to be higher than 0."
        await ctx.send(msg)


    @commands.command(pass_context=True, no_pm=True)
    async def give(self, ctx, user: discord.Member, cookies: int):
        """Gives another user your cookies"""
        author = ctx.message.author
        settings = self.check_guild_settings(author.guild)
        if user.bot:
            return await ctx.send("Nice try, us bots can't accept cookies from strangers.")
        if author.id == user.id:
            return await ctx.send("You can't give yourself cookies.")
        self.account_check(settings, author)
        self.account_check(settings, user)
        sender_cookies = settings["Players"][str(author.id)]["Cookies"]
        if 0 < cookies <= sender_cookies:
            settings["Players"][str(author.id)]["Cookies"] -= cookies
            settings["Players"][str(user.id)]["Cookies"] += cookies
            dataIO.save_json(self.file_path, self.system)
            y = ":cookie:" * cookies
            msg = "You gave **{}** cookies to {} \n {}".format(cookies, user.name, y)
        else:
            msg = "You don't have enough cookies in your account"

        await ctx.send(msg)

    @commands.command(pass_context=True, no_pm=True)
    async def cookie(self, ctx):
        """Obtain a random number of cookies. 12h cooldown"""
        author = ctx.message.author
        guild = ctx.message.guild
        action = "Cookie CD"
        settings = self.check_guild_settings(guild)
        self.account_check(settings, author)
        if await self.check_cooldowns(author.id, action, settings):
            weighted_sample = [1] * 152 + [x for x in range(49) if x > 1]
            cookies = random.choice(weighted_sample)
            y = ":cookie: " * cookies
            settings["Players"][str(author.id)]["Cookies"] += cookies
            dataIO.save_json(self.file_path, self.system)
            await ctx.send("You recieved {} cookie(s) from the cookie Gods! Nyaaaaaan!\n {}".format(cookies, y))

    @commands.command(pass_context=True, no_pm=False, ignore_extra=False)
    async def jar(self, ctx):
        """See how many cookies are in your jar."""
        author = ctx.message.author
        guild = ctx.message.guild
        settings = self.check_guild_settings(guild)
        self.account_check(settings, author)
        cookies = settings["Players"][str(author.id)]["Cookies"]
        y= ":cookie:" * cookies
        await ctx.send("Yori sees you have **{}** cookies in the jar. "
                               "\n {} ".format(cookies,y))

    @commands.command(pass_context=True, no_pm=True)
    async def steal(self, ctx, user: discord.Member=None):
        """Steal cookies from another user. 2h cooldown."""
        author = ctx.message.author
        guild = author.guild
        action = "Steal CD"
        settings = self.check_guild_settings(author.guild)
        self.account_check(settings, author)

        if user is None:
            user = self.random_user(settings, author, guild)

        if user == "Fail":
            pass
        elif user.bot:
            return await ctx.send("You can't steal from me because I am a cookie god.\nYou "
                                      "can try stealing from one of the mortals though :grin:")

        if await self.check_cooldowns(author.id, action, settings):
            msg = self.steal_logic(settings, user, author)
            await ctx.send(":spy: Yori is on the prowl to steal :cookie:")
            await asyncio.sleep(4)
            await ctx.send(msg)

    async def check_cooldowns(self, userid, action, settings):
        path = settings["Config"][action]
        if abs(settings["Players"][str(userid)][action] - int(time.perf_counter())) >= path:
            settings["Players"][str(userid)][action] = int(time.perf_counter())
            dataIO.save_json(self.file_path, self.system)
            return True
        elif settings["Players"][str(userid)][action] == 0:
            settings["Players"][str(userid)][action] = int(time.perf_counter())
            dataIO.save_json(self.file_path, self.system)
            return True
        else:
            s = abs(settings["Players"][str(userid)][action] - int(time.perf_counter()))
            seconds = abs(s - path)
            remaining = self.time_formatting(seconds)
            await ctx.send("I can't do that for you YET. You still have:\n{}".format(remaining))
            return False

    def steal_logic(self, settings, user, author):
        success_chance = random.randint(1, 100)
        if user == "Fail":
            msg = ":no_mouth: Nyaaaaaaaan! I couldn't find anyone with cookies!"
            return msg

        if str(user.id) not in settings["Players"]:
            self.account_check(settings, user)

        if settings["Players"][str(user.id)]["Cookies"] == 0:
            msg = (":cry: Nyaa! Yori is sorry, nothing but crumbs in this human's "
                   ":cookie: jar!")
        else:
            if success_chance <= 90:
                cookie_jar = settings["Players"][str(user.id)]["Cookies"]
                cookies_stolen = int(cookie_jar * 0.75)

                if cookies_stolen == 0:
                    cookies_stolen = 1

                stolen = random.randint(1, cookies_stolen)
                settings["Players"][str(user.id)]["Cookies"] -= stolen
                settings["Players"][str(author.id)]["Cookies"] += stolen
                dataIO.save_json(self.file_path, self.system)
                y = ":cookie:" * stolen
                msg = (":grin: You stole {} cookies from "
                       "{}! \n {}".format(stolen, user.name, y))
            else:
                msg = ":angry: Nyaa... Yori couldn't find their :cookie: jar!"
        return msg

    def random_user(self, settings, author, guild):
        filter_users = [guild.get_member(x) for x in settings["Players"]
                        if hasattr(guild.get_member(x), "name")]
        legit_users = [x for x in filter_users if str(x.id) != str(author.id) and x is not x.bot]

        users = [x for x in legit_users if settings["Players"][str(x.id)]["Cookies"] > 0]

        if not users:
            user = "Fail"
        else:
            user = random.choice(users)
            if user == user.bot:
                users.remove(user.bot)
                settings["Players"].pop(user.bot)
                dataIO.save_json(self.file_path, self.system)
                user = random.choice(users)
            self.account_check(settings, user)
        return user

    def account_check(self, settings, userobj):
        if str(userobj.id) not in settings["Players"]:
            settings["Players"][str(userobj.id)] = {"Cookies": 0,
                                               "Steal CD": 0,
                                               "Cookie CD": 0}
            dataIO.save_json(self.file_path, self.system)

    def time_formatting(self, seconds):
        # Calculate the time and input into a dict to plural the strings later.
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        data = PluralDict({'hour': h, 'minute': m, 'second': s})
        if h > 0:
            fmt = "{hour} hour{hour(s)}"
            if data["minute"] > 0 and data["second"] > 0:
                fmt += ", {minute} minute{minute(s)}, and {second} second{second(s)}"
            if data["second"] > 0 == data["minute"]:
                fmt += ", and {second} second{second(s)}"
            msg = fmt.format_map(data)
        elif h == 0 and m > 0:
            if data["second"] == 0:
                fmt = "{minute} minute{minute(s)}"
            else:
                fmt = "{minute} minute{minute(s)}, and {second} second{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s > 0:
            fmt = "{second} second{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s == 0:
            msg = "None"
        return msg

    def check_guild_settings(self, guild):
        if str(guild.id) not in self.system["guilds"]:
            self.system["guilds"][str(guild.id)] = {"Players": {},
                                                 "Config": {"Steal CD": 5,
                                                            "Cookie CD": 5}
                                                 }
            dataIO.save_json(self.file_path, self.system)
            print("Creating default heist settings for guild: {}".format(guild.name))
            path = self.system["guilds"][str(guild.id)]
            return path
        else:
            path = self.system["guilds"][str(guild.id)]
            return path


def check_folders():
    if not os.path.exists("data/cookie"):
        print("Creating data/cookie folder...")
        os.makedirs("data/cookie")


def check_files():
    default = {"guilds": {}}

    f = "data/cookie/cookie.json"
    if not dataIO.is_valid_json(f):
        print("Creating default cookie.json...")
        dataIO.save_json(f, default)


def setup(bot):
    check_folders()
    check_files()
    n=Cookie(bot)
    bot.add_cog(n)