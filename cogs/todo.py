from discord.ext import commands
import asyncio

def to_emoji(c):
    base = 0x0031
    return chr(base + c)

class Todo:
    """To-Do Lists"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def todo(self, ctx, *, subject):
        """Create a to-do list with a subject and react with emojis when each item is completed.
        """

        # a list of messages to delete when we're all done
        messages = [ctx.message]
        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) <= 100

        for i in range(20):
            messages.append(await ctx.send(f'Add item or {ctx.prefix}cancel to publish list.'))

            try:
                entry = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                break

            messages.append(entry)

            if entry.clean_content.startswith(f'{ctx.prefix}cancel'):
                break

            answers.append((to_emoji(i), entry.clean_content))

        try:
            await ctx.channel.delete_messages(messages)
        except:
            pass # oh well

        answer = '\n'.join(f'{keycap}: {content}' for keycap, content in answers)
        actual_poll = await ctx.send(f'{ctx.author} asks: {subject}\n\n{answer}')
        for emoji, _ in answers:
            await actual_poll.add_reaction(emoji)

    @todo.error
    async def todo_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send('Missing the subject.')

    @commands.command()
    @commands.guild_only()
    async def quicktodo(self, ctx, *subjects_and_tasks: str):
        """Makes a to-do list quickly.

        The first argument is the subject and the rest are the tasks.
        """

        if len(subjects_and_tasks) < 3:
            return await ctx.send('Need at least 1 subject with 2 tasks.')
        elif len(subjects_and_tasks) > 21:
            return await ctx.send('You can only have up to 20 tasks.')

        perms = ctx.channel.permissions_for(ctx.me)
        if not (perms.read_message_history or perms.add_reactions):
            return await ctx.send('Need Read Message History and Add Reactions permissions.')

        subject = subjects_and_tasks[0]
        tasks = [(to_emoji(e), v) for e, v in enumerate(subjects_and_tasks[1:])]

        try:
            await ctx.message.delete()
        except:
            pass

        body = "\n".join(f"{key}: {c}" for key, c in tasks)
        todo = await ctx.send(f'{ctx.author} asks: {subject}\n\n{body}')
        for emoji, _ in tasks:
            await todo.add_reaction(emoji)

def setup(bot):
    bot.add_cog(Todo(bot))
