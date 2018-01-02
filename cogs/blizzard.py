import asyncio
import os
import re
from copy import copy
from numbers import Number

import aiohttp
import discord
from cogs.utils import checks
from discord.ext import commands
from discord.ext.commands import formatter

from .utils.dataIO import dataIO
from bs4 import BeautifulSoup
import bleach

# Special thanks to judge2020 for telling me about this method for getting
# patch notes. https://github.com/judge2020/BattleNetUpdateChecker
# Embed menus are modified version of the menu cog written by Awoonar Dust#7332
# https://github.com/Lunar-Dust/Dusty-Cogs/


class Blizzard:

    """Blizzard Game Utilities"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings_path = "data/blizzard/settings.json"
        self.settings = dataIO.load_json(self.settings_path)
        self.base_url = 'https://us.battle.net/connect/en/app/'
        self.product_url = '/patch-notes?productType='
        self.wowtoken_url = 'http://wowtokenprices.com'
        self.patch_urls = {
            'hearthstone': 'https://us.battle.net/hearthstone/en/blog/',
            'overwatch': 'https://playoverwatch.com/en-us/game/patch-notes/pc/',
            'starcraft2': 'https://us.battle.net/sc2/en/game/patch-notes/',
            'warcraft': 'https://us.battle.net/wow/en/game/patch-notes/',
            'diablo3': 'https://us.battle.net/d3/en/game/patch-notes/',
            'hots': 'https://us.battle.net/heroes/en/blog/'
        }
        self.header = {"User-Agent": "flapjackcogs/1.0"}
        self.patch_header = {'User-Agent': 'Battle.net/1.0.8.4217'}
        self.abbr = {
            'hearthstone': 'wtcg',
            'overwatch': 'Pro',
            'starcraft2': 'sc2',
            'warcraft': 'WoW',
            'diablo3': 'd3',
            'hots': 'heroes'
        }
        self.thumbs = {
            'hearthstone': 'http://i.imgur.com/uK0AlGb.png',
            'overwatch': 'https://i.imgur.com/YZ4w2ey.png',
            'starcraft2': 'https://i.imgur.com/ErDVIMO.png',
            'warcraft': 'https://i.imgur.com/nrGZdB7.png',
            'diablo3': 'https://i.imgur.com/5WYDHHZ.png',
            'hots': 'https://i.imgur.com/NSMkOsA.png'
        }
        self.emoji = {
            "next": "\N{BLACK RIGHTWARDS ARROW}",
            "back": "\N{LEFTWARDS BLACK ARROW}",
            "no": "\N{CROSS MARK}"
        }
        self.expired_embed = discord.Embed(title="This menu has exipred due "
                                           "to ina*btivity.")

    async def show_menu(self, ctx, message, messages, page):
        if message:
            await message.edit(content=messages[page])
            return message
        else:
            return await ctx.send(messages[page])

    async def _info_menu(self, ctx, messages, **kwargs):
        page = kwargs.get("page", 0)
        timeout = kwargs.get("timeout", 30.0)
        emoji = kwargs.get("emoji", self.emoji)
        message = kwargs.get("message", None)
        choices = len(messages)

        reactions_needed = True if message is None else False

        message = await self.show_menu(ctx, message, messages, page)

        if reactions_needed:
            await message.add_reaction(str(emoji['back']))
            await message.add_reaction(str(emoji['no']))
            await message.add_reaction(str(emoji['next']))

        def check(reaction, user):
            return reaction.message.id == message.id and user == ctx.message.author
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
            if reaction is None:
                return [None, message]

            reacts = {v: k for k, v in emoji.items()}
            react = reacts[reaction.emoji]

            if react == "next":
                page += 1
            elif react == "back":
                page -= 1
            elif react == "no":
                return ["no", message]

            if page < 0:
                page = choices - 1

            if page == choices:
                page = 0

        except asyncio.TimeoutError:
            await ctx.send("Menu timed out - please use the command again to use the menu.")
            return [None, message]
            self.paginating = False

        return await self._info_menu(
            ctx, messages,
            page=page,
            timeout=timeout,
            emoji=emoji,
            message=message)

    def dictgrab(self, my_dict, *keys):
        temp_dict = copy(my_dict)
        for key in keys:
            temp_dict = temp_dict.get(key)
            if temp_dict is None:
                return '-'
        if isinstance(temp_dict, Number):
            return str(round(temp_dict))
        else:
            return '-'

    @commands.command()
    @checks.is_owner()
    async def blizzardkey(self, ctx, key: str):
        """Set the cog's battle.net API key, required for Diablo statistics.
        (get one at https://dev.battle.net/)
        Use a direct message to keep the key secret."""

        self.settings['apikey'] = key
        dataIO.save_json(self.settings_path, self.settings)
        await ctx.send('API key set.')

    @commands.command()
    @checks.is_owner()
    async def patchinfoformat(self, ctx, form: str):
        """Set the format of the patch notes posted in chat.
        paged: post a single message with navigation menu
        full: post full notes in multiple messages
        embed: post a summary with link to full notes"""

        accept = ['paged', 'full', 'embed']
        if form in accept:
            self.settings['notes_format'] = form
            dataIO.save_json(self.settings_path, self.settings)
            await ctx.send("Patch notes format set to `{}`.".format(form))
        else:
            await ctx.send("`{}` is not a valid format. Please choose "
                               "`{}`, `{}`, or `{}`.".format(form, accept[0],
                                                             accept[1], accept[2]))

    @commands.command()
    @checks.is_owner()
    async def patchtimeout(self, ctx, timeout: int):
        """Set the timeout period (sec) of the patch notes reaction menus.
        Only relevant for 'paged' or 'embed' mode."""

        min_max = (5, 3600)
        if min_max[0] <= timeout <= min_max[1]:
            self.settings['notes_timeout'] = timeout
            dataIO.save_json(self.settings_path, self.settings)
            # Need str() casting?
            await ctx.send("Timeout period set to `{} sec`.".format(timeout))
        else:
            await ctx.send("Please choose a duration between "
                               "{} and {} seconds.".format(min_max[0], min_max[1]))

    @commands.command()
    async def setblizzardtag(self, ctx, tag: str):
        """Set your battletag"""

        pattern = re.compile(r'.#\d{4,5}\Z')
        if pattern.search(tag) is None:
            await ctx.send("That doesn't look like a valid battletag.")
            return
        uid = str(ctx.message.author.id)
        self.settings['battletags'][uid] = tag
        dataIO.save_json(self.settings_path, self.settings)
        await ctx.send("Your battletag has been set.")

    @commands.command()
    async def clearblizzardtag(self, ctx):
        """Remove your battletag"""

        uid = str(ctx.message.author.id)
        if self.settings['battletags'].pop(uid, None) is not None:
            await ctx.send("Your battletag has been removed.")
        else:
            await ctx.send("I had no battletag stored for you.")
        dataIO.save_json(self.settings_path, self.settings)

    @commands.command()
    async def hearthstonepatch(self, ctx):
        """Latest Hearthstone patch notes"""
        await self.format_patch_notes(ctx, 'hearthstone')

    @commands.command()
    async def owstats(self, ctx, tag: str=None, region: str=None):
        """Overwatch stats for your battletag (case sensitive and PC only!).
        If battletag is ommitted, bot will use your battletag if stored.
        Region is optional and will autodetect with this priority: kr>eu>us

        Example: [p]owstats CoolDude#1234 us
        """

        uid = str(ctx.message.author.id)
        # Little hack to detect if region was entered, but not battletag
        if (tag in ['kr', 'eu', 'us']) and (region is None):
            region = tag
            tag = None

        if tag is None:
            tag = self.settings['battletags'].get(uid)
            if tag is None:
                await ctx.send('You did not provide a battletag '
                                   'and I do not have one stored for you.')
                return

        tag = tag.replace("#", "-")
        url = 'https://owapi.net/api/v3/u/' + tag + '/stats'
        async with aiohttp.ClientSession(headers=self.header) as session:
            async with session.get(url) as resp:
                stats = await resp.json()

        if 'error' in stats:
            await ctx.send('Could not fetch your statistics. '
                               'Battletags are case sensitive '
                               'and require a 4 or 5-digit identifier '
                               '(e.g. CoolDude#1234)'
                               'Or, you may have an invalid tag '
                               'on file.')
            return

        if region is None:
            if stats['us']:
                region = 'us'
            elif stats['eu']:
                region = 'eu'
            elif stats['kr']:
                region = 'kr'
            else:
                await ctx.send('That battletag has no stats in any region.')
                return

        region_full = self.ow_full_region(region)

        if region not in stats.keys() or stats[region] is None:
            await ctx.send('That battletag exists, but I could not '
                               'find stats for the region specified. '
                               'Try a different region '
                               '<us/eu/kr> or leave that field blank '
                               'so I can autodetect the region.')
            return

        url = 'https://playoverwatch.com/en-us/career/pc/' + region + '/' + tag
        tag = tag.replace("-", "#")

        qplay = stats[region]['stats']['quickplay']
        if qplay is None:
            qplay_stats = "*No matches played*"
            thumb_url = self.thumbs['overwatch']
        else:
            thumb_url = qplay['overall_stats']['avatar']
            qplay_stats = ''.join(['**Wins:** ', self.dictgrab(qplay, 'game_stats', 'games_won'),
                                   '\n**Best Kill Streak:** ', self.dictgrab(qplay, 'game_stats', 'kill_streak_best'),
                                   '\n**Most Elims:** ', self.dictgrab(qplay, 'game_stats', 'eliminations_most_in_game'),
                                   '\n**Kills Per Death:** ', self.dictgrab(qplay, 'game_stats', 'kpd')])

        comp = stats[region]['stats']['competitive']
        footer = None
        if comp is None:
            comp_stats = "*No matches played*"
            tier = None
        elif comp['overall_stats']['comprank'] is None:
            comp_stats = "*Not ranked*"
            tier = None
        else:
            tier = comp['overall_stats']['tier']
            footer = "For more visit https://playoverwatch.com/"
            comp_stats = ''.join(['SR: ' + str(comp['overall_stats']['comprank']),
                                  '\n**Wins:** ', self.dictgrab(comp, 'game_stats', 'games_won'),
                                  '\n**Best Kill Streak:** ', self.dictgrab(comp, 'game_stats', 'kill_streak_best'),
                                  '\n**Most Elims:** ', self.dictgrab(comp, 'game_stats', 'eliminations_most_in_game'),
                                  '\n**Kills Per Death:** ', self.dictgrab(comp, 'game_stats', 'kpd')])

        icon_url = self.ow_tier_icon(tier)

        embed = discord.Embed(title='Overwatch Stats (PC-' + region_full + ')', color=0xFAA02E)
        embed.set_author(name=tag, url=url, icon_url=icon_url)
        embed.set_thumbnail(url=thumb_url)
        embed.add_field(name='__Competitive__', value=comp_stats, inline=True)
        embed.add_field(name='__Quick Play__', value=qplay_stats, inline=True)
        if footer is not None:
            embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    def ow_tier_icon(self, tier: str):
        return {
            'bronze': 'https://i.imgur.com/B4IR72H.png',
            'silver': 'https://i.imgur.com/1mOpjRc.png',
            'gold': 'https://i.imgur.com/lCTsNwo.png',
            'platinum': 'https://i.imgur.com/nDVHAbp.png',
            'diamond': 'https://i.imgur.com/fLmIC70.png',
            'master': 'https://i.imgur.com/wjf0lEc.png',
            'grandmaster': 'https://i.imgur.com/5ApGiZs.png',
        }.get(tier, self.thumbs['overwatch'])

    def ow_full_region(self, region: str):
        return {
            'kr': 'Asia',
            'eu': 'Europe',
            'us': 'US',
        }.get(region, ' ')

    @commands.command()
    async def owpatch(self, ctx):
        await self.format_patch_notes(ctx, 'overwatch')

    @commands.command()
    async def sc2patch(self, ctx):
        """Latest Starcraft2 patch notes"""
        await self.format_patch_notes(ctx, 'starcraft2')

    @commands.command()
    async def wowpatch(self, ctx):
        """Latest World of Warcraft patch notes"""
        await self.format_patch_notes(ctx, 'warcraft')

    @commands.command()
    async def wowtoken(self, ctx, *, realm):
        """WoW Token Prices"""

        url = self.wowtoken_url

        if realm.lower() not in ['us', 'eu', 'cn', 'tw', 'kr']:
            await ctx.send("'" + realm + "' is not a valid realm.")
            return

        await self.print_token(url, self.wow_full_region(realm))

    def wow_full_region(self, region: str):
        # Works only with wowtokenprices.com
        return {
            'kr': 'korea',
            'eu': 'eu',
            'us': 'us',
            'cn': 'china',
            'tw': 'taiwan'
        }.get(region, ' ')


    @commands.command()
    async def diablo3patch(self, ctx):
        """Latest Diablo3 patch notes"""
        await self.format_patch_notes(ctx, 'diablo3')

    @commands.command()
    async def diablo3stats(self, ctx, tag: str=None, region: str=None):
        """Diablo3 stats for your battletag.
        If battletag is ommitted, bot will use your battletag if stored.

        Example: [p]diablo3 stats CoolDude#1234
        """

        uid = str(ctx.message.author.id)

        # Little hack to detect if region was entered, but not battletag
        if tag is not None and tag.lower() in ['kr', 'eu', 'us', 'tw']\
                and region is None:
            region = tag
            tag = None

        if tag is None:
            if uid in self.settings['battletags']:
                tag = self.settings['battletags'][uid]
            else:
                await ctx.send('You did not provide a battletag '
                                   'and I do not have one stored for you.')
                return

        if 'apikey' not in self.settings:
            await ctx.send('The bot owner has not provided a '
                               'battle.net API key, which is '
                               'required for Diablo 3 stats.')
            return

        if region is not None:
            region = region.lower()
        if region == 'us':
            locale = 'en_US'
        elif region == 'eu':
            locale = 'en_GB'
        elif region == 'kr':
            locale = 'ko_KR'
        elif region == 'tw':
            locale = 'zh_TW'
        else:
            locale = 'en_US'
            region = 'us'

        key = self.settings['apikey']
        tag = tag.replace("#", "-")
        url = 'https://' + region + '.api.battle.net/d3/profile/'\
              + tag + '/?locale=' + locale + '&apikey=' + key

        async with aiohttp.ClientSession(headers=self.header) as session:
            async with session.get(url) as resp:
                stats = await resp.json()

        if 'code' in stats:
            await ctx.send("I coulnd't find Diablo 3 stats for that battletag.")
            return

        tag = tag.replace("-", "#") + ' (' + region.upper() + ')'
        thumb_url = self.thumbs['diablo3']

        paragon = ''.join([':leaves:Seasonal: ', str(stats['paragonLevelSeason']),
                           '\n:leaves:Seasonal Hardcore: ', str(stats['paragonLevelSeasonHardcore']),
                           '\nNon-Seasonal: ', str(stats['paragonLevel']),
                           '\nNon-Seasonal Hardcore: ', str(stats['paragonLevelHardcore'])])

        hero_txt = ''
        for hero in stats['heroes']:
            hero_txt += ''.join([':leaves:' if hero['seasonal'] else '', hero['name'],
                                 ' - lvl ', str(hero['level']), ' ', hero['class'],
                                 ' - hardcore' if hero['hardcore'] else '',
                                 ' (RIP)\n' if hero['dead'] else '\n'])

        if not hero_txt:
            await ctx.send("You don't have any Diablo 3 heroes.")
            return

        kills = "Lifetime monster kills: " + str(stats['kills']['monsters'])

        embed = discord.Embed(title='Diablo 3 Stats', color=0xCC2200)
        embed.set_author(name=tag)
        embed.set_thumbnail(url=thumb_url)
        embed.add_field(name='__Paragon__', value=paragon, inline=False)
        embed.add_field(name='__Heroes__', value=hero_txt, inline=False)
        embed.set_footer(text=kills)
        await ctx.send(embed=embed)

    @commands.command()
    async def hotspatch(self, ctx):
        """Latest Heroes of the Storm patch notes"""
        await self.format_patch_notes(ctx, 'hots')

    async def format_patch_notes(self, ctx, game: str=None):
        url = ''.join([self.base_url,
                       self.abbr[game],
                       self.product_url,
                       self.abbr[game]])
        tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div']
        attr = {'div': 'class'}
        async with aiohttp.get(url, headers=self.patch_header) as response:
            dirty = await response.text()
        clean = bleach.clean(dirty, tags=tags, attributes=attr, strip=True)
        soup = BeautifulSoup(clean, "html.parser")
        # Preserving this list structure, in case we ever want to switch to
        # scraping the actual game websites for multiple notes
        notes = soup.find_all('div', class_="patch-notes-interior")
        note_list = []
        for note in notes:
            # Format each patch note into an array of messages using Paginator
            pager = formatter.Paginator(prefix='```markdown', suffix='```', max_size=1000)
            # Custom headers for sucky patch notes that have none
            if game == "starcraft2":
                text = "STARCRAFT 2 PATCH NOTES"
                pager.add_line(text + '\n' + '='*len(text))
            elif game == "warcraft":
                text = "WORLD OF WARCRAFT PATCH NOTES"
                pager.add_line(text + '\n' + '='*len(text))
            elif game == "hearthstone":
                # Convert first paragraph to h1
                note.p.name = 'h1'
            elif game == "overwatch":
                pass
            elif game == "diablo3":
                text = "DIABLO 3 PATCH NOTES"
                pager.add_line(text + '\n' + '='*len(text))
            elif game == "hots":
                text = "HEROES OF THE STORM PATCH NOTES"
                pager.add_line(text + '\n' + '='*len(text))

            for child in note.children:
                if child.name == 'h1':
                    # This is a patch notes title, with date.
                    text = child.get_text()
                    pager.add_line(text + '\n' + '='*len(text))
                elif str(child.name).startswith('h'):
                    # Thid is a patch notes section heading.
                    text = child.get_text()
                    pager.add_line('\n' + text + '\n' + '-'*len(text))
                elif child.name == 'p':
                    # This is a plain paragraph of patch notes.
                    text = child.get_text()
                    if text.strip():
                        text = '> ' + text if len(text) < 80 else text
                        pager.add_line('\n' + text)
                elif child.name == 'li':
                    # A list is about to follow.
                    pager.add_line('')
                    self.walk_list(child, pager, -1)
                else:
                    # Space reserved for future cases of "something else"
                    pass
            note_list.append(pager.pages)

        if self.settings.setdefault('notes_format', 'paged') == 'paged':
            result = await self._info_menu(ctx, note_list[0],
                timeout=self.settings.setdefault('notes_timeout', 60))
            if result[0] == "no":
                await result[1].delete()
            else:
                return
        elif self.settings['notes_format'] == 'full':
            await self.say_full_notes(note_list[0])
        else:
            # Extract title and body, remove markdown formatting line between
            split = note_list[0][0].split('\n', 3)
            title = split[1]
            # Remove \n```
            body = split[3][:-4]
            embed = discord.Embed(title=title, url=self.patch_urls[game], color=0x00B4FF)
            embed.set_thumbnail(url=self.thumbs[game])
            embed.add_field(name='Summary', value=body, inline=False)
            await ctx.send(embed=embed)

    def walk_list(self, child, pager, count):
        try:
            for grandchild in child.contents:
                self.walk_list(grandchild, pager, count + 1)
        except AttributeError:
            if child.string.strip():
                pager.add_line('  '*count + '*' + ' ' + child.string.strip())

    async def say_full_notes(self, pages):
        for page in pages:
            await ctx.send(page)
            await asyncio.sleep(1)

    async def print_token(self, ctx, url, realm):

        thumb_url = 'http://wowtokenprices.com/assets/wowtokeninterlaced.png'

        try:
            async with aiohttp.get(url, headers=self.header) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")

            data = soup.find('div', class_=realm + '-region-div')
            desc = data.div.a.h3.text
            buy_price = data.div.find('p', class_='money-text').text
            trend = data.div.find('span', class_='money-text-small').text
            # Update time broken, returns --:-- -- when requested by bot
            #updated = data.div.find('p', id=realm + '-datetime').text

            embed = discord.Embed(title='WoW Token Info', description=desc, colour=0xFFD966)
            embed.set_thumbnail(url=thumb_url)
            embed.add_field(name='Buy Price', value=buy_price, inline=False)
            embed.add_field(name='Change', value=trend, inline=False)
            #embed.set_footer(text='Updated: ' + updated)

            await ctx.send(embed=embed)

        except:
            await ctx.send("Error finding WoW token prices.")


def check_folders():
    folder = "data/blizzard"
    if not os.path.exists(folder):
        print("Creating {} folder...".format(folder))
        os.makedirs(folder)


def check_files():
    default = {'battletags': {}}
    if not dataIO.is_valid_json("data/blizzard/settings.json"):
        print("Creating default blizzard settings.json...")
        dataIO.save_json("data/blizzard/settings.json", default)


def setup(bot):
    try:
        check_folders()
        check_files()
        n = Blizzard(bot)
        bot.add_cog(n)
    except:
        error_text = ("Make sure beautifulsoup4 and bleach are installed."
                      "\n`pip install beautifulsoup4`"
                      "\n`pip install bleach`")
        raise RuntimeError(error_text)