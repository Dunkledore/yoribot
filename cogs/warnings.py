import asyncpg
import discord
from discord.ext import commands
import datetime

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
        alterquery = "UPDATE warnconfig SET muted_count = $2 WHERE guild_id = $1"

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
        alterquery = "UPDATE warnconfig SET muted_role = $2 WHERE guild_id = $1"

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
        alterquery = "UPDATE warnconfig SET banned_count = $2 WHERE guild_id = $1"

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
        alterquery = "UPDATE warnconfig SET report_channel = $2 WHERE guild_id = $1"

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
                    role = discord.utils.get(ctx.guild.roles, id=settings["muted_role"])
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

        embed = discord.Embed(description=discord.Embed.Empty, title=discord.Embed.Empty)
        embed.set_author(name="Logs for {}".format(member.name), icon_url="http://bit.ly/2rnwE4T")

        if warnings:
            embed.add_field(name="Warnings", value=warnings)

        if notes:
            embed.add_field(name="Notes", value=notes)

        await ctx.send(embed=embed)

    async def on_reaction_add(self, reaction, user):

        cog = self.bot.get_cog("Stats")
        hook = cog.webhook() 

        try:

            if reaction.emoji != '\U0000274c':
                return

            query = "SELECT * FROM warnconfig WHERE guild_id = $1"

            settings = await self.bot.pool.fetchrow(query, reaction.message.guild.id)

            if not settings:
                return

            if not settings["report_channel"]:
                return
            channel = self.bot.get_channel(settings["report_channel"])
            if not channel:
                return

            time = datetime.datetime.now()
            embed = discrd.Embed(title="New User Report", description=discord.Embed.Empty)
            embed.add_field(name="Reported by", value=user.mention)
            embed.add_field(name="Reported user", value=reaction.message.author.mention)
            embed.add_field(name="Reported content", value=reaction.message.content)
            embed.add_field(name="Time", value=time)
            embed.set_footer(text="User the reaction to approve, deny or note the report")
            message = await ctx.send(embed=embed)


            cross = "\N{NEGATIVE SQUARED CROSS MARK}"
            tick = "\N{WHITE HEAVY CHECK MARK}"
            note = "\N{Spiral Note Pad}"
            await message.add_reaction(tick)
            await message.add_reaction(cross)
            await message.add_reaction(note)


            def check(reaction, user):
                return message.id == reaction.message.id and reaction in ["\N{NEGATIVE SQUARED CROSS MARK}","\N{WHITE HEAVY CHECK MARK}","\N{Spiral Note Pad}"]

            reaction2, user2 = self.bot.wait_for("reaction_add", check=check)


            if reacion.emoji == cross:
                return

            if reacion.emoji == tick:
                warning = True

            if reaction.emoji == note:
                warning = False



            insertquery = "INSERT INTO warnings (guild_id, mod_id, user_id, reason, warning) VALUES ($1, $2, $3, $4, $5)"

            await self.bot.pool.execute(insertquery, reaction.message.guild.id, user2.id, reaction.message.author.id, reaction.message.content, warning)
            await channel.send(embed=self.bot.success("Warning Added"))

            query = "SELECT count(*) FROM warnings WHERE guild_id = $1 AND user_id = $2 and warning = $3"
            warning_count = await self.bot.pool.fetchval(query, reaction.message.guild.id, reaction.message.author.id, True)

            if settings["muted_role"]:
                if settings["muted_count"]:
                    if warning_count >= settings["muted_count"]:
                        role = discord.utils.get(reaction.message.guild.roles, id=settings["muted_role"])
                        if role:
                            await reaction.message.author.add_roles(role)

            if settings["banned_count"]:
                if warning_count >= settings["banned_count"]:
                    await reaction.message.author.ban(reason="Automatic Ban see Warning log")   

        except Exception as e:
            await hook.send(str(e))









    #@commands.command()
    #async def report(self, ctx, member: discord.Member, reason):
    #   """Annonymously report a user to the mods"""








def setup(bot: commands.Bot):
    n = Warnings(bot)
    bot.add_cog(n)
