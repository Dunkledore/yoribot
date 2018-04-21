from discord.ext import commands
import asyncio
import asyncpg
import traceback
import discord
import inspect
import textwrap
from contextlib import redirect_stdout
import io
from .utils import checks
from .utils.paginator import FieldPages

# to expose to the eval command
import datetime
from collections import Counter

class Admin:
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()
        self.tox_words = ["fag","fagging","faggitt","faggot","faggs","fagot","fagots","fags","fannyfucker","n1gga","n1gger","nigg3r","nigg4h","nigga","niggah","niggas","niggaz","nigger","niggers","shitdick","I'm ugly","I look ugly","im ugly","im too ugly","i'm too ugly","kys","kill yourself","end yourself"]

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    async def __local_check(self, ctx):
        return True

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'
   
    @commands.command(hidden=True)
    @checks.is_developer()
    async def tox(self, ctx, guild_id : int, *, ignore_roles = None):
        role_names = ignore_roles.split(",")
        roles = []
        guild = self.bot.get_guild(guild_id)
        for role in role_names:
            actual_role = discord.utils.get(guild.roles, name=role)
            if not actual_role:
                await ctx.send("Role {} not found".format(role))
                return
            else:
                roles.append(actual_role)
        if not guild:
            await ctx.send(embed=self.bot.error("Guild not found"))
            return

        await ctx.send("Gathering data...")
        tox_number = 0
        words = {}
        tox_users = {}

        for channel in guild.text_channels:
            if guild.me in channel.members:
                async for message in channel.history(limit=5000):
                    try:
                        if message.content:
                            for word in self.tox_words:
                                if word.lower() in message.content.lower():
                                    if not any(role in message.author.roles for role in roles):
                                        tox_number += 1
                                        if word in words:
                                            words[word] += 1
                                        else:
                                            words[word] = 1
                                        if message.author in tox_users:
                                            tox_users[message.author].append(word)
                                        else:
                                            tox_users[message.author] = [word]
                    except Exception as e:
                        await ctx.send(e)


        embed = discord.Embed(title = "Tox Report for {}".format(guild.name), description = "number of offences {}".format(tox_number))
        em = discord.Embed(title="User tox report")
        for word, number in words.items():
            embed.add_field(name=word, value=number)
        for user, user_words in tox_users.items():
            value_str = ""
            for item in set(user_words):
                value_str += "{} - {}\n".format(item, user_words.count(item))
            em.add_field(name=user.name, value=value_str)
        await ctx.send(embed=embed)
        await ctx.send(embed=em)



    @commands.command(hidden=True)
    @checks.is_owner()
    async def leave(self, ctx, id : int):
        for guild in self.bot.guilds:
            if id == guild.id:
                await guild.leave()
                return
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ="You are not in that guild"))



    @commands.command(hidden=True)
    @checks.is_developer()
    async def ping(self, ctx):
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "🖧 Ping",
                                description ='Pong'))

    @commands.command(hidden=True)
    @checks.is_developer()
    async def guilds(self, ctx):
        """List of guilds the bot is in"""
        entries = {}
        counter = 1
        for guild in self.bot.guilds:
            string = "**ID:** "+ str(guild.id) + " **Owner:** " +guild.owner.name + "\n"
            entries[f'{str(counter)}. {guild.name}'] = string
            counter+= 1

        paginator = FieldPages(ctx, entries=list(entries.items()), per_page=5)
        paginator.embed.title = "🖧 Servers the Bot is In:"
        await paginator.paginate()

    @commands.command(hidden=True)
    @checks.is_admin()
    async def modrole(self, ctx, role: discord.Role):
        """Sets the mod role"""

        insertquery = "INSERT INTO mod_config (guild_id, mod_role) VALUES ($1, $2)"
        alterquery = "UPDATE mod_config SET mod_role = $2 WHERE guild_id = $1"

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, role.id)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, role.id)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description = 'Role set'))

    @commands.command(hidden=True)
    @checks.is_developer()
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description =f'```py\n{traceback.format_exc()}\n```'))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ="Plugin Loaded"))

    @commands.command(hidden=True)
    @checks.is_developer()
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description =f'```py\n{traceback.format_exc()}\n```'))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ="Plugin Unloaded"))

    @commands.command(name='reload', hidden=True)
    @checks.is_developer()
    async def _reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = f'```py\n{traceback.format_exc()}\n```'))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description ="Plugin Reloaded"))

    @commands.command(pass_context=True, hidden=True, name='eval')
    @checks.is_developer()
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = f'```py\n{e.__class__.__name__}: {e}\n```'))

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = f'```py\n{value}{traceback.format_exc()}\n```'))
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command(pass_context=True, hidden=True)
    @checks.is_developer()
    async def repl(self, ctx):
        """Launches an interactive REPL session."""
        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            '_': None,
        }

        if ctx.channel.id in self.sessions:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ='Already running a REPL session in this channel. Exit it with `quit`.'))
            return

        self.sessions.add(ctx.channel.id)
        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ Notice",
                                description = 'Enter code to execute or evaluate. `exit()` or `quit` to exit.'))

        def check(m):
            return m.author.id == ctx.author.id and \
                   m.channel.id == ctx.channel.id and \
                   m.content.startswith('`')

        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ Notice",
                                description = 'Exiting REPL session.'))
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "❕ Notice",
                                description = 'Exiting.'))
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = self.get_syntax_error(e)))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = f'```py\n{value}{traceback.format_exc()}\n```'
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'```py\n{value}{result}\n```'
                    variables['_'] = result
                elif value:
                    fmt = f'```py\n{value}\n```'

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = 'Content too big to be printed.'))
                    else:
                        await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description = fmt))
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = f'Unexpected error: `{e}`'))


    @commands.command(hidden=True)
    @checks.is_developer()
    async def sql(self, ctx, *, query: str):
        """Run some SQL."""
        # the imports are here because I imagine some people would want to use
        # this cog as a base for their other cog, and since this one is kinda
        # odd and unnecessary for most people, I will make it easy to remove
        # for those people.
        from .utils.formats import TabularData, Plural
        import time

        query = self.cleanup_code(query)

        is_multistatement = query.count(';') > 1
        if is_multistatement:
            # fetch does not support multiple statements
            strategy = ctx.db.execute
        else:
            strategy = ctx.db.fetch

        try:
            start = time.perf_counter()
            results = await strategy(query)
            dt = (time.perf_counter() - start) * 1000.0
        except Exception:
            return await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description = f'```py\n{traceback.format_exc()}\n```'))

        rows = len(results)
        if is_multistatement or rows == 0:
            return await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description =f'`{dt:.2f}ms: {results}`'))

        headers = list(results[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()

        fmt = f'```\n{render}\n```\n*Returned {Plural(row=rows)} in {dt:.2f}ms*'
        if len(fmt) > 2000:
            fp = io.BytesIO(fmt.encode('utf-8'))
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "⚠ Error",
                                description ='Too many results...'))
            await ctx.send(file=discord.File(fp, 'results.txt'))
        else:
            await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
                                title = "✅ Success",
                                description =fmt))

def setup(bot):
    bot.add_cog(Admin(bot))