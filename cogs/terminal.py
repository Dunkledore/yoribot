from subprocess import Popen, CalledProcessError, PIPE, STDOUT
from re import sub
from sys import argv
from os.path import exists, abspath, dirname
from os import makedirs, getcwd, chdir, listdir, popen as ospopen
from asyncio import sleep
from getpass import getuser
from platform import uname, python_version
from discord.ext import commands
from cogs.utils import checks
from cogs.utils.dataIO import dataIO
import asyncio

__author__ = 'Sentry#4141'


class terminal:
    """Repl like Terminal in discord"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json')
        self.prefix = self.settings['prefix']
        self.cc = self.settings['cc']
        self.os = self.settings['os']
        self.cos = self.settings['cos']
        self.enabled = self.settings['enabled']
        self.sessions = {}
        if "logs" in self.settings.keys():
            self.logsenabled = self.settings["logs"]["enabled"]
            self.logschannel = self.settings["logs"]["channel"]
        else:
            self.settings["logs"] = {"enabled": False, "channel": ""}
            dataIO.save_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json', self.settings)

    @commands.command(hidden=True)
    @checks.is_owner()
    async def cmddebug(self, ctx):
        """This command is for debugging only"""
        try:
            commithash = ospopen('git rev-parse --verify HEAD').read()[:7]
        finally:
            if not commithash:
                commithash = 'None'

        text = str('```'
                   'Bot Information\n\n'
                   'Bot name:           {}\n'
                   'Bot displayname:    {}\n'
                   'Bot directory        {}\n\n'
                   'Operating System:   {}\n'
                   'OS Version:         {}\n'
                   'Architecture:       {}\n\n'
                   'Python Version:     {}\n'
                   'Commit              {}\n'
                   '```'.format(ctx.message.guild.me.name,
                                ctx.message.guild.me.display_name,
                                abspath(dirname(argv[0])), uname()[0],
                                uname()[3], uname()[4], python_version(),
                                commithash))

        result = []
        in_text = text
        shorten_by = 12
        page_length = 2000
        num_mentions = text.count("@here") + text.count("@everyone")
        shorten_by += num_mentions
        page_length -= shorten_by
        while len(in_text) > page_length:
            closest_delim = max([in_text.rfind(d, 0, page_length)
                                 for d in ["\n"]])
            closest_delim = closest_delim if closest_delim != -1 else page_length
            to_send = in_text[:closest_delim].replace(
                "@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
            result.append(to_send)
            in_text = in_text[closest_delim:]

        result.append(in_text.replace(
            "@everyone", "@\u200beveryone").replace("@here", "@\u200bhere"))

        for page in result:
            await ctx.send(page)

    @commands.group(hidden=True)
    @checks.is_owner()
    async def system(self, ctx):
        """Returns system infromation"""
        await ctx.send('{} is running on {} {} using {}'
                       ''.format(ctx.message.guild.me.display_name,
                                 uname()[0], uname()[2], python_version()))

    @commands.command()
    @checks.is_owner()
    async def cmd(self, ctx):
        """Starts up the prompt"""
        if ctx.message.channel.id in self.sessions:
            await ctx.send('Already running a Terminal session '
                           'in this channel. Exit it with `exit()` or `quit`')
            return

        # Rereading the values that were already read in __init__ to ensure its always up to date
        try:
            self.settings = dataIO.load_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json')
        except:
            # Pretend its the worst case and reset the settings
            check_folder()
            check_file()
            self.settings = dataIO.load_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json')

        self.prefix = self.settings['prefix']
        self.cc = self.settings['cc']
        self.os = self.settings['os']

        self.sessions.update({ctx.message.channel.id: getcwd()})
        await ctx.send('Enter commands after {} to execute them.'
                       ' `exit()` or `quit` to exit.'.format(self.prefix.replace("`", "\\`")))

    @commands.group()
    @checks.is_owner()
    async def cmdsettings(self, ctx):
        """Settings for terminal"""
        if ctx.invoked_subcommand is None:
            pages = self.bot.formatter.format_help_for(ctx, ctx.command)
            for page in pages:
                await ctx.send(page)

    @cmdsettings.group(name="customcom")
    @checks.is_owner()
    async def _cc(self, ctx):
        """Custom commands for terminal"""
        await ctx.send('This feature is WIP')
        """
        if ctx.invoked_subcommand is None:
            pages = self.bot.formatter.format_help_for(ctx, ctx.command)
            for page in pages:
                await self.bot.send_message(ctx.message.channel, page)
                """

    @cmdsettings.command(name="os")
    @checks.is_owner()
    async def _os(self, ctx, os: str = None):
        """Set the prompt type of terminal to emulate another Operatingsystem.
        these 'emulations' arent 100% accurate on other Operatingsystems"""

        if os is None:
            pages = self.bot.formatter.format_help_for(ctx, ctx.command)
            for page in pages:
                await ctx.send(page)
            if self.cos == 'default':
                await ctx.send('```\nCurrent prompt type: {}[{}] ```\n'
                               ''.format(self.cos, uname()[0].lower()))
            else:
                await ctx.send('```\nCurrent prompt type: {} ```\n'.format(self.cos))
            return

        if not os.lower() in self.os and os != 'default':
            await ctx.send('Invalid prompt type.\nThe following once are valid:\n\n{}'
                           ''.format(", ".join(self.os)))
            return

        os = os.lower()

        self.cos = os
        self.settings['cos'] = os
        dataIO.save_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json', self.settings)
        await ctx.send('Changed prompt type to {} '.format(self.cos.replace("`", "\\`")))

    @cmdsettings.command(name="prefix")
    @checks.is_owner()
    async def _prefix(self, ctx, prefix: str = None):
        """Set the prefix for the Terminal"""

        if prefix is None:
            pages = self.bot.formatter.format_help_for(ctx, ctx.command)
            for page in pages:
                await ctx.send(page)
            await ctx.send('```\nCurrent prefix: {} ```\n'.format(self.prefix))
            return

        self.prefix = prefix
        self.settings['prefix'] = prefix
        dataIO.save_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json', self.settings)
        await ctx.send('Changed prefix to {} '.format(self.prefix.replace("`", "\\`")))

    @commands.command(name="sendlogs")
    @checks.is_owner()
    async def enablelogs(self, ctx):
        """Sets a channel system logs should be sent to."""
        self.settings["logs"]["enabled"] = True
        self.settings["logs"]["channel"] = str(ctx.message.channel.id)
        dataIO.save_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json', self.settings)
        await ctx.send("System logs will now be sent to this channel.")

    @commands.command(name="nologs")
    @checks.is_owner()
    async def disablelogs(self, ctx):
        """Disables sending system logs to a channel."""
        self.settings["logs"]["enabled"] = False
        self.settings["logs"]["channel"] = ""
        dataIO.save_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json', self.settings)
        await ctx.send("System logs will no longer be sent.")

    @commands.command(name="lastlogs")
    @checks.is_owner()
    async def sendlatestlogs(self,ctx):
        """Sends the last 10 log items."""
        try:
            output = Popen("journalctl -u yato -q -n", shell=True, stdout=PIPE, stderr=STDOUT).communicate()[0].decode("utf_8")
        except:
            return
        await ctx.send(f"```py\n{output}\n```")

    async def sendlogs(self):
        await self.bot.wait_until_ready()
        while True:
            if self.logsenabled:
                chan = self.bot.get_channel(int(self.logschannel))
                if chan is not None:
                    try:
                        output = \
                        Popen('journalctl -u yato -q -S "-10s"', shell=True, stdout=PIPE, stderr=STDOUT).communicate()[
                            0].decode("utf_8")
                    except:
                        return
                    await chan.send(f"```py\n{output}\n```")
            await asyncio.sleep(10)

    async def on_message(self, message):  # This is where the magic starts

        if message.channel.id in self.sessions and self.enabled:  # and message.author.id == self.bot.settings.owner: # DO NOT DELETE

            # TODO:
            #  Whitelist & Blacklists that cant be modified by the bot

            if not dataIO.is_valid_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json'):
                check_folder()
                check_file()
                self.settings = dataIO.load_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json')
                self.prefix = self.settings['prefix']
                self.cc = self.settings['cc']
                self.os = self.settings['os']
                self.cos = self.settings['cos']
                self.enabled = self.settings['enabled']

            if (message.content.startswith(self.prefix) or
                    message.content.startswith('debugprefixcmd')):
                if message.content.startswith(self.prefix):
                    command = message.content[len(self.prefix):]
                else:
                    command = message.content[len('debugprefixcmd'):]
                # check if the message starts with the command prefix
                while command.startswith(' '):
                    command = command[1:]

                if message.attachments:
                    command += ' ' + message.attachments[0]['url']

                if not command:  # if you have entered nothing it will just ignore
                    return

                if command in self.cc:
                    if self.cc[command][uname()[0].lower()]:
                        command = self.cc[command][uname()[0].lower()]
                    else:
                        command = self.cc[command]['linux']

                if (command == 'exit()' or
                            command == 'quit'):  # commands used for quiting cmd, same as for repl

                    # await self.bot.send_message(message.channel, 'Exiting.')
                    await message.channel.send("Exiting.")
                    self.sessions.pop(message.channel.id)
                    return
                elif commands == 'exit':
                    await message.channel.send("Exiting.")
                    return

                if "apt-get install" in command.lower() and not "-y" in command.lower():
                    command = "{} -y".format(command)  # forces apt-get to not ask for a prompt

                if command.startswith('cd ') and command.split('cd ')[1]:
                    path = command.split('cd ')[1]
                    try:
                        oldpath = abspath(dirname(argv[0]))
                        chdir(path)
                        self.sessions.update({message.channel.id: getcwd()})
                        await sleep(1)
                        chdir(oldpath)
                        return
                    except FileNotFoundError:
                        shell = 'cd: {}: Permission denied'.format(path)
                    except PermissionError:
                        shell = 'cd: {}: No such file or directory'.format(path)
                else:
                    try:
                        output = Popen(command, cwd=self.sessions[message.channel.id], shell=True, stdout=PIPE,
                                       stderr=STDOUT).communicate()[0]
                        error = False
                    except CalledProcessError as err:
                        output = err.output
                        error = True

                    shell = output.decode('utf_8')

                if shell == "" and not error:
                    return

                shell = sub('/bin/sh: .: ', '', shell)
                if "\n" in shell[:-2]:
                    shell = '\n' + shell

                if self.cos == 'default':
                    cos = uname()[0].lower()
                else:
                    cos = self.cos

                path = self.sessions[message.channel.id]
                username = getuser()
                system = uname()[1]
                if cos in self.os:
                    user = self.os[cos].format(
                        user=username, system=system, path=path)
                else:
                    user = self.os['linux'].format(user=username, system=system, path=path)

                result = []
                in_text = text = user + shell
                shorten_by = 12
                page_length = 2000
                num_mentions = text.count("@here") + text.count("@everyone")
                shorten_by += num_mentions
                page_length -= shorten_by
                while len(in_text) > page_length:
                    closest_delim = max([in_text.rfind(d, 0, page_length)
                                         for d in ["\n"]])
                    closest_delim = closest_delim if closest_delim != -1 else page_length
                    to_send = in_text[:closest_delim].replace(
                        "@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
                    result.append(to_send)
                    in_text = in_text[closest_delim:]

                result.append(in_text.replace(
                    "@everyone", "@\u200beveryone").replace("@here", "@\u200bhere"))

                # result = list(pagify(user + shell, shorten_by=12))

                for num, output in enumerate(result):
                    if num % 1 == 0 and num != 0:

                        note = await message.channel.send('There are still {} pages left.\n'
                                                          'Type `more` to continue.'
                                                          ''.format(len(result) - (num + 1)))
                        msg = await self.bot.wait_for("message", check=lambda m:
                        m.channel == message.channel and
                        m.author == message.author and
                        m.content == 'more', timeout=10.0)
                        try:
                            await note.delete()
                        except Exception:
                            pass

                        if msg is None:
                            return
                        else:
                            if output:
                                await message.channel.send(f"```Bash\n{output}```")
                    else:
                        if output:
                            await message.channel.send(f"```Bash\n{output}```")


def check_folder():
    if not exists(abspath(dirname(argv[0])) + '/data/terminal'):
        print("[Terminal]Creating data/terminal folder...")
        makedirs(abspath(dirname(argv[0])) + '/data/terminal')


def check_file():
    jdict = {
        "prefix": ">",
        "cc": {'test': {'linux': 'printf "Hello.\n'
                                 'This is a custom command made using the magic of python."',
                        'windows': 'echo Hello. '
                                   'This is a custom command made using the magic of python.'}
               },
        "os": {
            'windows': '{path}>',
            'linux': '{user}@{system}:{path} $ '
        },
        "cos": "default",
        "logs": {
            "enabled": False,
            "channel": ""
        },
        "enabled": True
    }

    if not dataIO.is_valid_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json'):
        print("[terminal]Creating default settings.json...")
        dataIO.save_json(abspath(dirname(argv[0])) + '/data/terminal/settings.json', jdict)


def setup(bot):
    check_folder()
    check_file()
    t = terminal(bot)
    bot.add_cog(t)
    bot.loop.create_task(t.sendlogs)
