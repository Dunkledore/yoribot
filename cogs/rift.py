import discord
from discord.ext import commands
from collections import namedtuple
from cogs.utils.chat_formatting import escape, pagify
from cogs.utils.dataIO import dataIO
from .utils import checks
import os

OpenRift = namedtuple("Rift", ['name','channels'])

def formatembed(m):
    em = discord.Embed(color=m.author.color, description=m.content)
    avatar = m.author.avatar_url
    author_name = m.author.nick+" ("+m.author.name+")" if m.author.nick else m.author.name
    em.set_author(name=author_name,icon_url=avatar)
    footer = "- sent from #"+m.channel.name+" in "+m.guild.name
    em.set_footer(text=footer)
    return em

class Rift:
    """Communicate with other servers/channels!"""

    def __init__(self, bot):
        self.bot = bot
        self.open_rifts = {}
        self.embeds = {}
        self.ready = False

    async def load_settings(self):
        await self.bot.wait_until_ready()
        allchannels = self.bot.get_all_channels()
        settings = dataIO.load_json("data/rift/settings.json")
        if "embeds" in settings.keys() and isinstance(settings["embeds"],dict):
            for e in settings["embeds"].keys():
                ch = self.bot.get_channel(e)
                if ch:
                    self.embeds[ch] = settings["embeds"][e]
                else:
                    print("Channel {} not found. It has been removed from the rift settings.".format(e))
        if "open_rifts" in settings.keys() and isinstance(settings["open_rifts"],dict):
            for r in settings["open_rifts"].keys():
                chs = []
                for rc in settings["open_rifts"][r]:
                    ch = self.bot.get_channel(int(rc))
                    if ch:
                        chs.append(ch)
                    else:
                        print("Channel {} not found. It has been removed from the rift \"{}\".".format(rc,r))
                if len(chs) < 2:
                    print("The rift \""+r+"\" has been closed due to removed channels.")
                else:
                    self.open_rifts[r] = chs
        self.save_settings()
        self.ready = True

    @commands.command(pass_context=True, no_pm=True)
    async def riftembeds(self, ctx, status : str):
        """Toggles Embeds for Rift messages in this channel. Specify on or off."""
        if not status.lower() in ["on","off"]:
            await self.bot.say("Please use `riftembeds on` or `riftembeds off`.")
        else:
            self.embeds[ctx.message.channel] = status.lower() == "on"
            self.save_settings()
            await ctx.send("Rift embeds for this channel have been turned "+status+".")

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_channels=True)
    async def riftopen(self, ctx, name, channel):
        """Makes you able to communicate with other channels through Red.

        This is cross-server. Specify the name of the rift and a channel to connect it to (name without # or id). More channels can be added to the rift later with riftconnect"""

        def check(m):
            try:
                print('5')
                if m.author != ctx.message.author:
                    return False
                if m.channel != ctx.message.channel:
                    return False
                return channels[int(m.content)]
            except:
                return False

        if name in self.open_rifts:
            await ctx.send("A rift with that name already exists. Please use another name.")
            return

        channels = self.bot.get_all_channels()
        channels = [c for c in channels
                    if c.name.lower() == channel or c.id == channel]
        channels = [c for c in channels if type(c) == discord.TextChannel]

        if not channels:
            await ctx.send("No channels found.")
            return       
        if len(channels) > 1:
            msg = "Multiple results found.\nChoose a server:\n"
            for i, channel in enumerate(channels):
                msg += "{} - {} ({})\n".format(i, channel.guild, channel.id)
            for page in pagify(msg):
                await ctx.send(page)
            choice = await self.bot.wait_for('message', check=check, timeout=30.0)
            if choice is None:
                await ctx.send("You haven't chosen anything.")

                return
            channel = channels[int(choice.content)]
        else:
            channel = channels[0]

        self.open_rifts[name] = [ctx.message.channel, channel]
        self.embeds.setdefault(ctx.message.channel, True)
        self.embeds.setdefault(channel, True)
        await ctx.send("A rift has been opened! Everything you say "
                           "will be relayed to connected channels.\n"
                           "Responses will be relayed here.\n"
                           "Use riftdisconnect to remove this channel from the rift, or"
                           "riftclose to close the rift.")
        self.save_settings()

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_channels=True)
    async def riftconnect(self, ctx, riftname, channel):
        """Connects a channel to the specified rift."""
       
        def check(m):
            try:
                if m.author != ctx.message.author:
                    return False
                if m.channel != ctx.message.channel:
                    return False
                return channels[int(m.content)]
            except:
                return False

        if riftname not in self.open_rifts:
            await ctx.send("That rift doesn't exist.")
            return
        if ctx.message.channel not in self.open_rifts[riftname]:
            await ctx.send("This channel doesn't belong to that rift.")
            return

        channels = self.bot.get_all_channels()
        channels = [c for c in channels
                    if c.name.lower() == channel or c.id == channel]
        channels = [c for c in channels if type(c) == discord.TextChannel]

        if not channels:
            await ctx.send("No channels found.")
            return

        if len(channels) > 1:
            msg = "Multiple results found.\nChoose a server:\n"
            for i, chan in enumerate(channels):
                msg += "{} - {} ({})\n".format(i, chan.guild, chan.id)
            for page in pagify(msg):
                await ctx.send(page)
            choice = await self.bot.wait_for('message', timeout=30.0, check=check)
            if choice is None:
                await ctx.send("You haven't chosen anything.")
                return
            ch = channels[int(choice.content)]
        else:
            ch = channels[0]

        if ch in self.open_rifts[riftname]:
            await ctx.send("The channel already belongs to that rift.")
            return
        self.open_rifts[riftname].append(ch)
        self.embeds.setdefault(ch, True)
        await ctx.send("The channel is now connected to the rift.")
        self.save_settings()

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_channels=True)
    async def riftclose(self, ctx, riftname):
        """Closes the specified rift. Can only be used from a channel belonging to that rift."""
        if riftname not in self.open_rifts:
            await ctx.send("That rift doesn't exist.")
            return
        if ctx.message.channel not in self.open_rifts[riftname]:
            await ctx.send("This channel doesn't belong to that rift.")
            return
        del self.open_rifts[riftname]
        await ctx.send("Rift closed.")
        self.save_settings()

    @commands.command()
    async def printchannels(self):
        for e in self.embeds.keys():
            print(e)

    @commands.command(pass_context=True,no_pm=True)
    @checks.mod_or_permissions(manage_channels=True)
    async def riftlist(self,ctx):
        """ Lists all the rifts this channel is in. """
        rnames = []
        for r in self.open_rifts.keys():
            if ctx.message.channel in self.open_rifts[r]:
                rnames.append(r)
        if len(rnames) == 0:
            await ctx.send("This channel belongs to no rifts.")
        else:
            s = "This channel belongs to the following rifts: \n"
            for n in rnames:
                s += "**{}**, ".format(n)
            s = s[:-2]
            await ctx.send(s)

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_channels=True)
    async def riftdisconnect(self,ctx,riftname):
        """Disconnects this channel from the specified rift."""
        if riftname not in self.open_rifts:
            await ctx.send("That rift doesn't exist.")
            return
        if ctx.message.channel not in self.open_rifts[riftname]:
            await ctx.send("This channel doesn't belong to that rift.")
            return
        if len(self.open_rifts[riftname]) == 2:
            await ctx.send("Only one channel connected to the rift. Closing...")
            if self.open_rifts[riftname][0] == ctx.message.channel:
                await self.open_rifts[riftname][1].send("This channel has been disconnected from the rift '{}' due to being the only member in it.".format(riftname))
            else:
                await self.open_rifts[riftname][0].send("This channel has been disconnected from the rift '{}' due to being the only member in it.".format(riftname))
            del self.open_rifts[riftname]
        else:
            self.open_rifts[riftname].remove(ctx.message.channel)
            await ctx.send("Disconnected from the rift.")
        self.save_settings()

    async def on_message(self, msg):
        if not self.ready:
            await self.load_settings()
        if msg.author == self.bot.user:
            return
        prefs = prefixes = tuple(self.bot.get_guild_prefixes(msg.guild))
        for p in prefs:
            if msg.content.startswith(p) and msg.content[len(p):].lower().split(" ")[0] in self.bot.commands:
                return
        orift = {k:v for k,v in self.open_rifts.items() if v}
        for rift in orift:
            if msg.channel in orift[rift]:
                for chan in orift[rift]:
                    if chan != msg.channel:
                        #try:
                        if self.embeds[chan]:
                            await chan.send(embed=formatembed(msg))
                        else:
                            message = escape(msg.content, mass_mentions=True)
                            await chan.send("**Rift Message** from {} in #{} on {}: \n\n{}".format((msg.author.nick+" ("+msg.author.name+")" if msg.author.nick else msg.author.name), msg.channel.name, msg.guild.name,message))
                        #except Exception as baseerr:
                        #    try:
                        #        await msg.channel.send("Couldn't send your message." + baseerr)
                        #    except:
                        #        print("Couldn't send the message. An exception occured: ",baseerr)

    def save_settings(self):
        settings = {"open_rifts":{},"embeds":{}}
        for r in self.open_rifts.keys():
            settings["open_rifts"][r] = []
            for c in self.open_rifts[r]:
                settings["open_rifts"][r].append(c.id)

        for c in self.embeds.keys():
            settings["embeds"][c.id] = self.embeds[c]

        dataIO.save_json("data/rift/settings.json",settings)


def setup(bot):
    if not os.path.exists("data/rift"):
        print("Creating data/rift folder")
        os.makedirs("data/rift")
    if not os.path.exists("data/rift/settings.json"):
        print("Creating data/rift/settings.json file...")
        dataIO.save_json("data/rift/settings.json", {"open_rifts":{},"embeds":{}})
    bot.add_cog(Rift(bot))
