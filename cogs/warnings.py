import asyncpg
import discord
from discord.ext import commands

from .utils import checks

 #create table warnconfig (id SERIAL, guild_id BIGINT, muted_count INT,  muted_role BIGINT, banned_count INT, report_channel INT)
 #create table warnings(id SERIAL, guild_id BIGINT, mod_id BIGINT, user_id BIGINT, reason TEXT, warning bool, date timestamp default current_timestamp)

class Warnings:

    """A warning system with automatic banning and muting """

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def mutedcount(self, ctx, number: int):
        """Set the amount of warnings before a muted role will be given to a user"""

        insertquery = "INSERT INTO warnconfig (guild_id, muted_count) VALUES ($1, $2)"
        alterquery = "UPDATE greet SET muted_count = $2 WHERE guild_id = $1"

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, number)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, number)
        await ctx.send(embed=self.bot.success("Muted Count Set"))

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def mutedrole(self, ctx, role: discord.Role):
        """Set the role to be given to a user upon an automatic muting"""

        insertquery = "INSERT INTO warnconfig (guild_id, muted_role) VALUES ($1, $2)"
        alterquery = "UPDATE greet SET muted_role = $2 WHERE guild_id = $1"

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, role.id)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, role.id)
        await ctx.send(embed=self.bot.success("Muted Role Set"))



    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def bannedcount(self, ctx, number: int):
        """Set the amount of warnings before a user will be banned"""

        insertquery = "INSERT INTO warnconfig (guild_id, banned_count) VALUES ($1, $2)"
        alterquery = "UPDATE greet SET banned_count = $2 WHERE guild_id = $1"

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, number)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, number)
        await ctx.send(embed=self.bot.success("Banned Count Set"))

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def reportchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel user reoprts should be sent to for approval"""

        insertquery = "INSERT INTO warnconfig (guild_id, report_channel) VALUES ($1, $2)"
        alterquery = "UPDATE greet SET report_channel = $2 WHERE guild_id = $1"

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, channel.id)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, channel.id)
        await ctx.send(embed=self.bot.success("Report Channel Set"))

    @commands.command()
    @commands.guild_only()
    @checks.is_mod()
    async def warn(self, ctx, member: discord.Member, reason):
        """Apply a warning to a user"""

        insertquery = "INSERT INTO warnings (guild_id, mod_id, user_id, reason, warning) VALUES ($1, $2, $3, $4, $5)"

        await ctx.db.execute(insertquery, ctx.guild.id, ctx.author.id, member.id, reason, True)
        await ctx.send(embed=self.bot.success("Warning Added"))

        query = "SELECT * FROM warnconfig WHERE guild_id = $1"

        settings = await ctx.db.fetchrow(query, ctx.guild.id)

        query = "SELECT count(*) FROM warnings WHERE guild_id = $1 AND user_id = $2 and warning = $3"
        warning_count = await ctx.db.fetchval(query, ctx.guild.id, member.id, True)

        if settings["muted_role"]:
            if settings["muted_count"]:
                if warning_count >= settings["muted_count"]:
                    role = discord.Utils.get(ctx.guild.roles, id=settings["muted_role"])
                    if role:
                        await member.add_roles(role)

        if settings["banned_count"]:
            if warning_count >= settings["banned_count"]:
                await member.ban(reason="Automatic Ban see Warning log")


    @commands.command()
    @commands.guild_only()
    @checks.is_mod()
    async def note(self, ctx, member: discord.Member, reason):
        """Apply a note to a user - Does not count towards their warning count"""

        insertquery = "INSERT INTO warnings (guild_id, mod_id, user_id, reason, warning) VALUES ($1, $2, $3, $4, $5)"

        await ctx.db.execute(insertquery, ctx.guild.id, ctx.author.id, member.id, reason, False)
        await ctx.send(embed=self.bot.success("Note Added"))

    @commands.command()
    @commands.guild_only()
    @checks.is_mod()
    async def log(self, ctx, member: discord.Member):
        """Shows all notes and warning for a user"""

        query = "SELECT * FROM warnings WHERE guild_id = $1 AND user_id = $2"

        results = await ctx.db.fetch(query, ctx.guild.id, member.id)

        warnings = ""
        notes = ""

        for result in results:
            mod = ctx.guild.get_member(result["mod_id"])
            if mod: 
                mod = mod.mention
            else:
                mod = "User with ID: {}".format(result["mod_id"])
            if result["warning"]:
                warnings += "{} - {} - {}\n".format(result["date"], mod, result["reason"])
            else:
                notes += "{} - {} - {}\n".format(result["date"], mod, result["reason"])

        embed = discord.Embed(description="Logs for {}".format(member.mention), title=discord.Embed.Empty)

        if warnings:
            embed.add_field(name="Warnings", value=warnings)

        if notes:
            embed.add_field(name="Notes", value=notes)

        await ctx.send(embed=embed)



    #@commands.command()
    #async def report(self, ctx, member: discord.Member, reason):
    #   """Annonymously report a user to the mods"""








def setup(bot: commands.Bot):
    n = Warnings(bot)
    bot.add_cog(n)
