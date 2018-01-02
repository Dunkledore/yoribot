import asyncpg
import discord
from discord.ext import commands

from .utils import checks


class Greet:

    """Sets up a channel where you can receive notifications of when people join, leave, are banned or unbanned."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def greeter(self, ctx, role: discord.Role):
        """Sets the role for people who can greet new members"""

        insertquery = "INSERT INTO greet (guild_id, greeter_role_id) VALUES ($1, $2)"
        alterquery = "UPDATE greet SET greeter_role_id = $2 WHERE guild_id = $1"

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, role.id)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, role.id)
        await ctx.send('Role set')

    @commands.command()
    @commands.guild_only()
    @checks.is_admin()
    async def greetrole(self, ctx, role: discord.Role):
        """Sets the role assigned to new members"""

        insertquery = "INSERT INTO greet (guild_id, greeted_role_id) VALUES ($1, $2)"
        alterquery = "UPDATE greet SET greeted_role_id = $2 WHERE guild_id = $1"

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, role.id)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, role.id)
        await ctx.send('Role set')

    @commands.command()
    @commands.guild_only()
    @checks.is_greeter()
    async def greet(self, ctx, member: discord.Member):
        """Assigns the greet role to a new member"""

        query = "SELECT * FROM greet WHERE guild_id = $1"
        results = await ctx.db.fetch(query, ctx.guild.id)
        if not results:
            await ctx.send("Greeted role not setup")
            return

        if not results[0]['greeted_role_id']:
            await ctx.send("Greeted role not setup")
            return

        role = discord.utils.get(ctx.message.guild.roles, id=int(results[0]['greeted_role_id']))
        await member.add_roles(role)
        await ctx.send(member.name + ' greeted')


def setup(bot: commands.Bot):
    n = Greet(bot)
    bot.add_cog(n)