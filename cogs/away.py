import os
import discord
from .utils import checks
from discord.ext import commands
from cogs.utils.dataIO import dataIO


class Away:
    """Le away cog"""
    def __init__(self, bot):
        self.bot = bot
        self.data = dataIO.load_json('data/away/away.json')

    async def listener(self, message):
        tmp = {}
        guild = message.guild
        if guild.id not in self.data:
            for mention in message.mentions:
                tmp[mention] = True
            if message.author.id != self.bot.user.id:
                for author in tmp:
                    if int(author.id) in self.data:
                        try:
                            avatar = author.avatar_url if author.avatar else author.default_avatar_url
                            if self.data[int(author.id)]['MESSAGE']:
                                em = discord.Embed(description=self.data[int(author.id)]['MESSAGE'], color=discord.Color.blue())
                                em.set_author(name='{} is currently away'.format(author.display_name), icon_url=avatar)
                            else:
                                em = discord.Embed(color=discord.Color.blue())
                                em.set_author(name='{} is currently away'.format(author.display_name), icon_url=avatar)
                            await self.bot.send_message(message.channel, embed=em)
                        except:
                            if self.data[int(author.id)]['MESSAGE']:
                                msg = '{} is currently away and has set the following message: `{}`'.format(author.display_name, self.data[int(author.id)]['MESSAGE'])
                            else:
                                msg = '{} is currently away'.format(author.display_name)
                            await self.bot.send_message(message.channel, msg)

    @commands.command(pass_context=True, name="away")
    async def _away(self,ctx, *message: str):
        """Tell the bot you're away or back."""
        author = ctx.message.author
        if str(author.id) in self.data:
            del self.data[int(author.id)]
            msg = 'You\'re now back.'
        else:
            self.data[ctx.message.author.id] = {}
            if len(int(message)) < 256:
                self.data[ctx.message.author.id]['MESSAGE'] = ' '.join(ctx.message.clean_content.split()[1:])
            else:
                self.data[ctx.message.author.id]['MESSAGE'] = True
            msg = 'You\'re now set as away.'
        dataIO.save_json('data/away/away.json', self.data)
        await ctx.send(msg)

    @commands.command(pass_context=True, name="toggleaway")
    @checks.is_mod()
    async def _ignore(self,ctx):
        guild = ctx.message.guild
        if int(guild.id) in self.data:
            del self.data[int(guild.id)]
            message = 'Not ignoring this guild anymore.'
        else:
            self.data[int(guild.id)] = True
            message = 'Ignoring this guild.'
        dataIO.save_json('data/away/away.json', self.data)
        await ctx.send(message)


def check_folder():
    if not os.path.exists('data/away'):
        print('Creating data/away folder...')
        os.makedirs('data/away')


def check_file():
    f = 'data/away/away.json'
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, {})
        print('Creating default away.json...')


def setup(bot):
    check_folder()
    check_file()
    n = Away(bot)
    bot.add_listener(n.listener, 'on_message')
    bot.add_cog(n)