import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
from bs4 import BeautifulSoup
import aiohttp
import os
import re
from urllib.parse import quote as urlencode
import datetime
import asyncio

try:
    from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageOps
except:
    raise RuntimeError("Can't load pillow. Run 'pip3 install pillow'.")

# fonts
font_file = "data/ffxiv/RobotoCondensed-Regular.ttf"
font_bold_file = "data/ffxiv/RobotoCondensed-Bold.ttf"


class FFXIV:
    """Collection of various FFXIV utilities."""

    def __init__(self, bot):
        # Versions: 1 - Initial. 2 - SB, 3 - SB (fixed)
        self.IMAGE_VERSION = 3
        self.bot = bot
        self.settings = dataIO.load_json("data/ffxiv/settings.json")
        self.fflogs_settings = dataIO.load_json("data/ffxiv/fflogs/settings.json")
        self.fflogs_data = dataIO.load_json("data/ffxiv/fflogs/data.json")
        if not "characters" in self.settings.keys():
            self.settings["characters"] = {}
            self.save_settings()
        if not "_nonmember" in self.settings["characters"].keys():
            self.settings["characters"]["_nonmember"] = {}
            self.save_settings()
        self.servers = {
            "Elemental": ["Aegis", "Atomos", "Carbuncle", "Garuda", "Gungnir", "Kujata", "Ramuh", "Tonberry", "Typhon",
                          "Unicorn"],
            "Gaia": ["Alexander", "Bahamut", "Durandal", "Fenrir", "Ifrit", "Ridill", "Tiamat", "Ultima", "Valefor",
                     "Yojimbo", "Zeromus"],
            "Mana": ["Anima", "Asura", "Belias", "Chocobo", "Hades", "Ixion", "Mandragora", "Masamune", "Pandaemonium",
                     "Shinryu", "Titan"],
            "Aether": ["Adamantoise", "Balmung", "Cactuar", "Coeurl", "Faerie", "Gilgamesh", "Goblin", "Jenova",
                       "Mateus", "Midgardsormr", "Sargatanas", "Siren", "Zalera"],
            "Primal": ["Behemoth", "Brynhildr", "Diabolos", "Excalibur", "Exodus", "Famfrit", "Hyperion", "Lamia",
                       "Leviathan", "Malboro", "Ultros"],
            "Chaos": ["Cerberus", "Lich", "Louisoix", "Moogle", "Odin", "Phoenix", "Ragnarok", "Shiva", "Zodiark",
                      "Omega"]
        }
        self.latestnews = {}
        self.newsupdatetime = None
        self.updatefrequency = datetime.timedelta(minutes=10)
        self.newsiconurls = {
            "maintenance": "https://img.finalfantasyxiv.com/lds/h/U/6qzbI-6AwlXAfGhCBZU10jsoLA.png",
            "notices": "https://img.finalfantasyxiv.com/lds/h/c/GK5Y3gQsnlxMRQ_pORu6lKQAJ0.png",
            "topics": "https://img.finalfantasyxiv.com/lds/h/W/_v7zlp4yma56rKwd8pIzU8wGFc.png",
            "status": "https://img.finalfantasyxiv.com/lds/h/4/8PRdUkaKFa8R5BKeQjRyItGoxY.png"
        }
        self.newsurls = {
            "topics": "https://na.finalfantasyxiv.com/lodestone/topics",
            "maintenance": "https://na.finalfantasyxiv.com/lodestone/news/category/2",
            "notices": "https://na.finalfantasyxiv.com/lodestone/news/category/1",
            "status": "https://na.finalfantasyxiv.com/lodestone/news/category/4"
        }

        newsTicker = self.run_in_bg(self.send_all_news)

    def run_in_bg(self, target, *, loop=None, executor=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        if callable(target):
            return loop.run_in_executor(executor,target)


    def save_settings(self):
        dataIO.save_json("data/ffxiv/settings.json", self.settings)

    def save_fflogs_settings(self):
        dataIO.save_json("data/ffxiv/fflogs/settings.json", self.fflogs_settings)

    async def embed(self, ctx, authortext="", desc="", col="", footer=""):
        colors = {"red": 0xE74C3C, "green": 0x2ECC71, "yellow": 0xF1C40F, "purple": 0x9B59B6, "blue": 0x3498DB,
                  "white": 0xFFFFFF, "darkred": 0x73261E}
        c = colors[col] if col in colors.keys() else 0x000000
        em = discord.Embed(color=c, description=desc)
        em.set_author(name=authortext, icon_url="https://i.imgur.com/n3tqR2E.png")
        em.set_footer(text=footer)
        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def ffxiv(self, ctx):
        """FFXIV command group."""
        if not ctx.invoked_subcommand:
            return

    def getDC(self, server):
        for dc in self.servers.keys():
            if server in self.servers[dc]:
                return dc
        return ""

    async def _xivdb(self, mode, **kwargs):
        url = "http://api.xivdb.com/" + mode
        if mode == "search":
            if len(kwargs.keys()) > 0:
                url += "?"
                for k in kwargs:
                    url += urlencode(str(k)) + "=" + urlencode(str(kwargs[k])) + "&"
                url = url[:-1]
        if mode in ["character", "item", "recipe"]:
            if not "id_" in kwargs:
                return {}
            else:
                url += "/" + urlencode(str(kwargs["id_"]))
        async with aiohttp.get(url) as r:
            try:
                d = await r.json()
                return d
            except:
                return {"__ERROR__": "Invalid JSON or no response"}

    def getlongname(self, shortname):
        d = {"PLD": "Paladin", "WAR": "Warrior", "DRK": "Dark Knight", "GLA": "Gladiator",
             "MRD": "Marauder", "WHM": "White Mage", "SCH": "Scholar", "AST": "Astrologian",
             "CNJ": "Conjurer", "MNK": "Monk", "DRG": "Dragoon", "NIN": "Ninja", "BLM": "Black Mage",
             "BRD": "Bard", "SMN": "Summoner", "MCH": "Machinist", "SAM": "Samurai", "RDM": "Red Mage",
             "PGL": "Pugilist", "LNC": "Lancer", "ROG": "Rogue", "THM": "Thaumaturge", "ARC": "Archer",
             "ACN": "Arcanist", "CRP": "Carpenter", "BSM": "Blacksmith", "ARM": "Armorer",
             "GSM": "Goldsmith", "WVR": "Weaver", "LTW": "Leatherworker", "ALC": "Alchemist",
             "CUL": "Culinarian", "MIN": "Miner", "BTN": "Botanist", "FSH": "Fisher"}
        return d[shortname] if shortname in d.keys() else ""

    def getshortname(self, longname):
        d = {"PLD": "Paladin", "WAR": "Warrior", "DRK": "Dark Knight", "GLA": "Gladiator",
             "MRD": "Marauder", "WHM": "White Mage", "SCH": "Scholar", "AST": "Astrologian",
             "CNJ": "Conjurer", "MNK": "Monk", "DRG": "Dragoon", "NIN": "Ninja", "BLM": "Black Mage",
             "BRD": "Bard", "SMN": "Summoner", "MCH": "Machinist", "SAM": "Samurai", "RDM": "Red Mage",
             "PGL": "Pugilist", "LNC": "Lancer", "ROG": "Rogue", "THM": "Thaumaturge", "ARC": "Archer",
             "ACN": "Arcanist", "CRP": "Carpenter", "BSM": "Blacksmith", "ARM": "Armorer",
             "GSM": "Goldsmith", "WVR": "Weaver", "LTW": "Leatherworker", "ALC": "Alchemist",
             "CUL": "Culinarian", "MIN": "Miner", "BTN": "Botanist", "FSH": "Fisher"}
        for a in d.keys():
            if longname.lower() == d[a].lower():
                return a
        return ""

    async def _charsearch(self, server, first, last):
        char = await self._xivdb("search", **{"string": first + " " + last, "server|et": server})
        if "__ERROR__" in char.keys():
            return char
        if char["characters"]["total"] > 0:
            return char["characters"]["results"][0]["id"]
        return ""

    async def _itemsearch(self, itemname):
        items = await self._xivdb("search", string=itemname, one="items")
        return items["items"]["results"]

    async def _recipesearch(self, recipename):
        recipes = await self._xivdb("search", string=recipename.replace("\"", ""), one="recipes", order_search="id",
                                    order_direction="asc")
        return recipes["recipes"]["results"]

    @ffxiv.group(name="news", invoke_without_command=True)
    async def ffxiv_news(self, ctx):
        """Lodestone news."""
        if not ctx.invoked_subcommand:
            return

    @ffxiv_news.command(ame="enable")
    async def news_enable(self, ctx, *, type):
        """Enable sending lodestone news in this channel. Type can be: notices, topics, maintenance, status or all."""
        if "news" not in self.settings.keys():
            self.settings["news"] = {}
        if ctx.guild.id not in self.settings["news"].keys():
            self.settings["news"][ctx.guild.id] = {}
        self.save_settings()
        newsset = self.settings["news"][ctx.guild.id]
        ch = ctx.channel.id
        if type.lower() not in ("notices", "topics", "maintenance", "status", "all"):
            await self.embed(ctx, "Lodestone News",
                             "Invalid type. Please use one of the following:\n`notices`, `topics`, `maintenance`, `status`, `all`.",
                             "red")
            return
        if ch in newsset.keys() and (type.lower() in newsset[ch] or "all" in newsset[ch]):
            await self.embed(ctx, "Lodestone News", "Already sending those news here.", "red")
            return
        if type.lower == "all" or len(newsset[ch]) == 3:
            newsset[ch] = ["all"]
            await self.embed(ctx, "Lodestone News", "Now sending all lodestone news to this channel.", "green")
        else:
            newsset[ch].append(type.lower())
            await self.embed(ctx, "Lodestone News", "Now sending lodestone " + type.lower() + (
                " news" if type.lower in ["maintenance", "status"] else "") + "in this channel.", "green")
        self.save_settings()

    @ffxiv_news.command(name="disable")
    async def news_disable(self, ctx, *, type):
        """Disable sending lodestone news in this channel. Type can be: notices, topics, maintenance, status or all."""
        if "news" not in self.settings.keys():
            self.settings["news"] = {}
        if ctx.guild.id not in self.settings["news"].keys():
            self.settings["news"][ctx.guild.id] = {}
        self.save_settings()
        newsset = self.settings["news"][ctx.guild.id]
        ch = ctx.channel.id
        if ch not in newsset.keys() or type.lower() not in newsset[ch]:
            await self.embed(ctx, "Lodestone News", "No news are sent in this channel.", "red")
            return
        if type.lower() not in ("notices", "topics", "maintenance", "status", "all"):
            await self.embed(ctx, "Lodestone News",
                             "Invalid type. Please use one of the following:\n`notices`, `topics`, `maintenance`, `status`, `all`.",
                             "red")
            return
        if type.lower == "all" or len(newsset[ch]) == 1:
            newsset.pop(ch, "")
            await self.embed(ctx, "Lodestone News", "Now not sending any news in this channel.", "green")
        else:
            newsset[ch].remove(type.lower())
            await self.embed(ctx, "Lodestone News", "Not sending lodestone " + type.lower() + (
                " news" if type.lower in ["maintenance", "status"] else "") + "in this channel anymore.", "green")
        self.save_settings()

    async def collectnews(self):
        url = "http://xivdb.com/assets/lodestone.json"
        async with aiohttp.ClientSession().get(url) as r:
            d = await r.json()
            return d

    async def update_news(self, ctx):
        if ctx is not None:
            await ctx.send("Updating...")  # DEBUG
        try:
            d = await self.collectnews()
            self.latestnews = {"maintenance": sorted(d["maintenance"], key=lambda k: k["time"],reverse=True),
                               "topics": sorted(d["topics"], key=lambda k: k["time"],reverse=True),
                               "status": sorted(d["status"], key=lambda k: k["time"],reverse=True),
                               "notices": sorted(d["notices"], key=lambda k: k["time"],reverse=True)}
            self.format_news()
            self.newsupdatetime = datetime.datetime(2017, 1, 1).utcnow()
            if ctx is not None:
                await ctx.send("Updated.")  # DEBUG
        except Exception as e:
            self.latestnews = {"__ERROR__": str(e)}
            return

    def format_news(self):
        if self.latestnews is None or "__ERROR__" in self.latestnews.keys() or self.latestnews == {}:
            return
        for item in self.latestnews["topics"]:
            soup = BeautifulSoup(item["html"], "html.parser")
            item["text"] = soup.get_text()

    def get_news_after(self, timestamp):
        if self.latestnews is None or "__ERROR__" in self.latestnews.keys() or self.latestnews == {}:
            return
        news = {"topics": [], "notices": [], "maintenance": [], "status": []}
        for type in self.latestnews.keys():
            # "2017-11-18 17:20:35"
            for item in self.latestnews[type]:
                itemtime = datetime.datetime().strptime(item["time"], "%Y-%m-%d %H:%M:%S")
                if itemtime > timestamp:
                    news[type].append(item)
        return news

    @ffxiv_news.command(name="latest")
    async def latest_news(self, ctx, type="all", count=1):
        """Sends the latest count (max. 20, 5 for `all`) news of the given type to this channel. Type can be: notices, topics, maintenance, status or all."""

        count = int(count)
        if type.lower() not in ("notices", "topics", "maintenance", "status", "all"):
            await self.embed(ctx, "Lodestone News",
                             "Invalid type. Please use one of the following:\n`notices`, `topics`, `maintenance`, `status`, `all`.",
                             "red")
            return
        await ctx.send("Getting the latest " + str(count) + " " + type + " news.")  # DEBUG
        if self.newsupdatetime is None or self.newsupdatetime < datetime.datetime(2017,1,1).utcnow() - self.updatefrequency:
            await self.update_news(ctx)
        else:  # DEBUG
            await ctx.send("No update needed.")
        if "__ERROR__" in self.latestnews.keys():
            await ctx.send("Error updating:" + self.latestnews["__ERROR__"])  # DEBUG
            return
        if count < 1:
            count = 1
        if count > 20 or (type == "all" and count > 5):
            count = 5 if type == "all" else 20
        await ctx.send(f"Sending the latest {count} {type} news.")  # DEBUG
        if type == "all":
            for t in self.latestnews.keys():
                for i in range(count):
                    await ctx.send(embed=self.newsembed(ctx, self.latestnews[t][i], t))
        else:
            for i in range(count):
                await ctx.send(embed=self.newsembed(ctx, self.latestnews[type][i], type))

    async def newsembed(self, ctx, newsitem, type):
        titles = {"maintenance": "Maintenance", "notices": "Notice", "topics": "Topic", "status": "Status"}
        em = discord.Embed(color=0x73261E,
                           title=("" if "tag" not in newsitem.keys() or newsitem["tag"] == "" else newsitem[
                                                                                                       "tag"] + " ") +
                                 "Lodestone News: "+newsitem["title"],
                           url=newsitem["url"], description="" if "text" not in newsitem.keys() else newsitem["text"])
        if "banner" in newsitem.keys():
            em.set_image(url=newsitem["banner"])
        em.set_author(name=titles[type], url=self.newsurls[type], icon_url=self.newsiconurls[type])
        em.set_footer(text=newsitem["time"] + " (UTC)")
        return em

    async def send_all_news(self):
        while True:
            self.update_news(None)
            newsset = self.settings["news"]
            now = datetime.datetime(2017,1,1).utcnow()
            before = now - self.updatefrequency
            news = self.get_news_after(before)
            for guildid in newsset.keys():
                guild = self.bot.get_guild(guildid)
                if guild is not None:
                    for ch in newsset[guild].keys():
                        chan = guild.get_channel(ch)
                        if chan is not None:
                            for type in news.keys():
                                if newsset[guild][ch] == "all" or type in newsset[guild][ch]:
                                    for item in news[type]:
                                        await chan.send(self.newsembed(item, type))
            await asyncio.sleep(self.updatefrequency.seconds)

    @ffxiv.command()
    async def recipe(self, ctx, *, itemname):
        """Displays a recipe. Provide item name or recipe ID."""
        recipeid = ""
        m = re.compile("^\s*(\d+)\s*$").match(itemname)
        if m:
            recipeid = m.group(1)
        else:
            recipes = await self._recipesearch(itemname)
            if len(recipes) == 0:
                await self.embed(ctx, "FFXIV Recipe helper", "Couldn't find a recipe with that name", "red")
                return
            if len(recipes) > 1:
                embedtext = "**Found more than one recipe that matches your search**\nPlease use the full item name or recipe id.\n\n"
                for r in recipes:
                    embedtext += "**{}** - {} ({})\n".format(r["id"], r["name"], self.getshortname(r["class_name"]))
                await self.embed(ctx, "FFXIV Recipe helper", embedtext, "yellow")
                return
            else:
                recipeid = str(recipes[0]["id"])
        recipe = await self._xivdb("recipe", id_=recipeid)
        if "error" in recipe.keys():
            await self.embed(ctx, "XIVDB Error", recipe["error"], "red")
            return
        await self.draw_recipe(recipe)
        await ctx.message.channel.send(file=discord.File("data/ffxiv/{}.tmp.png".format(recipeid)))
        try:
            os.remove("data/ffxiv/{}.tmp.png".format(recipeid))
        except:
            pass

    @ffxiv.command()
    async def status(self, ctx, server=None):
        """Displays FFXIV server status."""
        url = "http://na.finalfantasyxiv.com/lodestone/worldstatus/"
        async with aiohttp.get(url) as r:
            soup = BeautifulSoup(await r.text(), 'html.parser')
            st = {}
            if soup.find(class_="maintenance__text"):
                await self.embed(ctx, "FFXIV Server Status",
                                 "**Lodestone is down for maintenance.**\n This usually means the servers are ***OFFLINE***.",
                                 "red")
                return
            for s in soup.find_all(class_="item-list__worldstatus"):
                st[s.h3.text.strip()] = 1 if s.find("p").text.find("Online") != -1 else 0
            if not server:
                if len([0 for x in st.keys() if st[x] == 0]) == 0:
                    await self.embed(ctx, "FFXIV Server Status", "**All servers are currently *ONLINE***", "green")
                elif len([0 for x in st.keys() if st[x] == 1]) == 0:
                    await self.embed(ctx, "FFXIV Server Status", "**All servers are currently *OFFLINE***", "red")
                else:
                    text = "Some servers are currently offline (**online**, ~~offline~~):\n\n"
                    for dc in self.servers.keys():
                        text += "***{}***:\n".format(dc)
                        for s in self.servers[dc]:
                            if st[s] == 1:
                                text += "**" + s + "**, "
                            else:
                                text += "~~" + s + "~~, "
                        text = text[:-2] + "\n\n"
                    await self.embed(ctx, "FFXIV Server Status", text, "yellow")
            else:
                server = server.title()
                if self.getDC(server) == "":
                    await self.embed(ctx, "FFXIV Server Status", "That server doesn't exist.", "red")
                else:
                    d = "**" + server + "** is currently " + ("**ONLINE**" if st[server] == 1 else "**ONLINE**")
                    await self.embed(ctx, "FFXIV Server Status", d, "green" if st[server] == 1 else "red")

    @ffxiv.command()
    async def iam(self, ctx, server, firstname, lastname):
        """Tell me who your character on FFXIV is!"""
        server = server.title()
        if self.getDC(server) == "":
            await self.embed(ctx, "FFXIV Character Info", "That server doesn't exist.", "red")
        else:
            charid = await self._charsearch(server, firstname, lastname)
            if isinstance(charid, dict):
                await self.embed(ctx, "XIVDB Error", charid["__ERROR__"], "red")
                return
            if charid == "":
                await self.embed(ctx, "FFXIV Character Info", "I couldn't find that character.", "red")
            else:
                if not ctx.message.author.id in self.settings["characters"].keys() or not isinstance(
                        self.settings["characters"][str(ctx.message.author.id)], dict):
                    self.settings["characters"][str(ctx.message.author.id)] = {"id": charid}
                self.settings["characters"][str(ctx.message.author.id)]["id"] = charid
                self.save_settings()
                await self.embed(ctx, "FFXIV Character Info", "Your character has been saved successfully!", "green")

    @ffxiv.command()
    async def deleteme(self, ctx):
        """Forget about your character."""
        if not str(ctx.message.author.id) in self.settings["characters"].keys():
            await self.embed(ctx, "FFXIV Character Info", "No character saved.", "red")
            return
        del self.settings["characters"][str(ctx.message.author.id)]
        self.save_settings()
        await self.embed(ctx, "FFXIV Character Info", "Character Info deleted. Who were you again?", "green")

    @ffxiv.command()
    async def charinfo(self, ctx, server, firstname, lastname):
        """Find out more about a character."""
        server = server.title()
        if self.getDC(server) == "":
            await self.embed(ctx, "FFXIV Character Info", "That server doesn't exist.", "red")
        else:
            charid = await self._charsearch(server, firstname, lastname)
            if isinstance(charid, dict):
                await self.embed(ctx, "XIVDB Error", charid["__ERROR__"], "red")
                return
            if charid == "":
                await self.embed(ctx, "FFXIV Character Info", "I couldn't find that character.", "red")
            else:
                if not "_nonmember" in self.settings["characters"].keys():
                    self.settings["characters"]["_nonmember"] = {}
                if not str(charid) in self.settings["characters"]["_nonmember"].keys() or not isinstance(
                        self.settings["characters"]["_nonmember"][str(charid)], dict):
                    self.settings["characters"]["_nonmember"][str(charid)] = {}
                    self.save_settings()
                charinfo = await self._xivdb("character", id_=charid)
                if "error" in charinfo.keys():
                    await self.embed(ctx, "FFXIV Character Info: XIVDB Error", charinfo["error"], "red")
                    return
                draw = 0
                if not "img_ver" in self.settings["characters"]["_nonmember"][str(charid)].keys() or int(
                        self.settings["characters"]["_nonmember"][str(charid)]["img_ver"]) != self.IMAGE_VERSION:
                    draw = 1
                if not "dh" in self.settings["characters"]["_nonmember"][str(charid)].keys() or \
                                self.settings["characters"]["_nonmember"][str(charid)]["dh"] != charinfo["data_hash"]:
                    self.settings["characters"]["_nonmember"][str(charid)]["dh"] = charinfo["data_hash"]
                if draw == 1:
                    await self.draw_profile(charinfo)
                    self.settings["characters"]["_nonmember"][str(charid)]["img_ver"] = self.IMAGE_VERSION
                    self.save_settings()
                with open("data/ffxiv/profiles/{}.png".format(charid), "rb") as f:
                    await ctx.message.channel.send(file=discord.File(f))

    @ffxiv.command()
    async def whoami(self, ctx):
        """Don't remember who you are? I'll help you find yourself!"""
        if not str(ctx.message.author.id) in self.settings["characters"].keys():
            await self.embed(ctx, "FFXIV Character Info", "No character saved.", "red")
            return
        charinfo = await self._xivdb("character", id_=self.settings["characters"][str(ctx.message.author.id)]["id"])
        if "error" in charinfo.keys():
            await self.embed(ctx, "FFXIV Character Info: XIVDB Error", charinfo["error"], "red")
            return
        draw = 0
        charid = str(self.settings["characters"][str(ctx.message.author.id)]["id"])
        if not str(self.settings["characters"][str(ctx.message.author.id)]["id"]) in self.settings["characters"][
            "_nonmember"].keys():
            self.settings["characters"]["_nonmember"][charid] = {"dh": charinfo["data_hash"]}
            draw = 1
        if not "dh" in self.settings["characters"]["_nonmember"][charid].keys():
            self.settings["characters"]["_nonmember"][charid]["dh"] = charinfo["data_hash"]
            draw = 1
        if not "img_ver" in self.settings["characters"]["_nonmember"][charid].keys() or int(
                self.settings["characters"]["_nonmember"][charid]["img_ver"]) != self.IMAGE_VERSION:
            draw = 1
        dh = self.settings["characters"]["_nonmember"][charid]["dh"]
        if dh == "" or dh != charinfo["data_hash"]:
            self.settings["characters"]["_nonmember"][charid]["dh"] = charinfo["data_hash"]
            draw = 1
        if draw == 1:
            await self.draw_profile(charinfo)
            self.settings["characters"]["_nonmember"][charid]["img_ver"] = self.IMAGE_VERSION
            self.save_settings()
        with open("data/ffxiv/profiles/{}.png".format(charinfo["data"]["id"]), "rb") as f:
            await ctx.message.channel.send(file=discord.File(f))

    @ffxiv.command()
    async def whois(self, ctx, user: discord.User):
        """Find out who your friend is in-game!"""
        if not str(user.id) in self.settings["characters"].keys():
            await self.embed(ctx, "FFXIV Character Info", "No character saved.", "red")
            return
        charinfo = await self._xivdb("character", id_=self.settings["characters"][str(user.id)]["id"])
        if "error" in charinfo.keys():
            await self.embed(ctx, "FFXIV Character Info: XIVDB Error", charinfo["error"], "red")
            return
        draw = 0
        charid = str(self.settings["characters"][str(user.id)]["id"])
        if not str(self.settings["characters"][str(user.id)]["id"]) in self.settings["characters"]["_nonmember"].keys():
            self.settings["characters"]["_nonmember"][charid] = {"dh": charinfo["data_hash"]}
            draw = 1
        if not "dh" in self.settings["characters"]["_nonmember"][charid].keys():
            self.settings["characters"]["_nonmember"][charid]["dh"] = charinfo["data_hash"]
            draw = 1
        dh = self.settings["characters"]["_nonmember"][charid]["dh"]
        if dh == "" or dh != charinfo["data_hash"]:
            self.settings["characters"]["_nonmember"][charid]["dh"] = charinfo["data_hash"]
            draw = 1
        if not "img_ver" in self.settings["characters"]["_nonmember"][charid].keys() or int(
                self.settings["characters"]["_nonmember"][charid]["img_ver"]) != self.IMAGE_VERSION:
            draw = 1
        if draw == 1:
            self.settings["characters"]["_nonmember"][charid]["img_ver"] = self.IMAGE_VERSION
            await self.draw_profile(charinfo)
            self.save_settings()
        with open("data/ffxiv/profiles/{}.png".format(charinfo["data"]["id"]), "rb") as f:
            await ctx.message.channel.send(file=discord.File(f))

    async def draw_profile(self, cdata):
        regular_fnt = ImageFont.truetype(font_bold_file, 22)
        name_small_fnt = ImageFont.truetype(font_bold_file, 24)
        name_verysmall_fnt = ImageFont.truetype(font_bold_file, 22)
        name_fnt = ImageFont.truetype(font_bold_file, 28)
        title_fnt = ImageFont.truetype(font_file, 16)
        level_fnt = ImageFont.truetype(font_file, 12)
        minion_fnt = ImageFont.truetype(font_file, 16)
        minionamt_fnt = ImageFont.truetype(font_bold_file, 13)
        current_level_fnt = ImageFont.truetype(font_file, 20)
        nameday_fnt = ImageFont.truetype(font_file, 14)
        race_fnt = ImageFont.truetype(font_file, 14)
        id_fnt = ImageFont.truetype(font_file, 10)
        server_fnt = ImageFont.truetype(font_file, 12)
        uid = cdata["data"]["id"]

        def _write_text(text, init_x, y, font, fill):
            write_pos = init_x
            for char in text:
                draw.text((write_pos, y), char, font=font, fill=fill)
                write_pos += font.getsize(char)[0]

        def _progressbar(init_x, init_y, width, height, bg, fg, percent):
            draw.rectangle([(init_x, init_y), (init_x + width - 1, init_y + height - 1)], fill=bg)
            if percent > 0:
                draw.rectangle(
                    [(init_x + 1, init_y + 1), (init_x + int(percent / 100 * (width - 2)), init_y + height - 2)],
                    fill=fg)

        def _center_text(text, init_x, init_y, width, height, font, fill):
            dims = [0, 0]
            for char in text:
                d = font.getsize(char)
                dims[0] += d[0]
                dims[1] = max(dims[1], d[1])
            inx = init_x + width / 2 - dims[0] / 2
            iny = init_y + height / 2 - dims[1] / 2
            _write_text(text, inx, iny, font, fill)

        def _right_text(text, max_x, init_y, font, fill):
            w = 0
            for char in text:
                w += font.getsize(char)[0]
            _write_text(text, max_x - w, init_y, font, fill)

        async with aiohttp.get(cdata["avatar"]) as r:
            image = await r.content.read()
        with open("data/ffxiv/profiles/{}.tmp.png".format(uid), "wb") as f:
            f.write(image)

        result = Image.new("RGBA", (400, 300), (255, 255, 255, 0))
        process = Image.new("RGBA", (400, 300), (255, 255, 255, 0))
        # process_text = Image.new("RGBA", (400,300),(255,255,255,0))
        fg_image = Image.open("data/ffxiv/profilebg.png").convert("RGBA")
        char_image = Image.open("data/ffxiv/profiles/{}.tmp.png".format(uid)).convert("RGBA")

        char_image = char_image.resize((90, 90), Image.ANTIALIAS)
        result.paste(char_image, (4, 7))
        result = Image.alpha_composite(result, fg_image)
        draw = ImageDraw.Draw(process)

        # guardian
        guardianpath = "data/ffxiv/images/" + cdata["data"]["guardian"]["name"].replace(" ", "_").replace(",",
                                                                                                          "_") + ".png"
        if not os.path.exists(guardianpath):
            async with aiohttp.get(cdata["data"]["guardian"]["icon"]) as r:
                gimg = await r.content.read()
            with open(guardianpath, "wb") as f:
                f.write(gimg)
        guardian_image = Image.open(guardianpath).convert("RGBA")
        process.paste(guardian_image, (33, 145))

        # current class/job
        process.paste(Image.open(
            "data/ffxiv/images/" + cdata["data"]["active_class"]["role"]["name"].lower().replace(" ",
                                                                                                 "") + ".png").convert(
            "RGBA"), (315, 95))

        # progress
        _progressbar(205, 118, 102, 5, (0, 0, 0, 255), (20, 140, 40, 255),
                     int(cdata["data"]["active_class"]["progress"]["exp"]["percent"]))

        # minions, mounts:
        _progressbar(205, 139, 102, 18, (0, 0, 0, 255), (20, 140, 40, 255), int(cdata["extras"]["mounts"]["percent"]))
        _progressbar(205, 163, 102, 18, (0, 0, 0, 255), (20, 140, 40, 255), int(cdata["extras"]["minions"]["percent"]))

        # gc
        if cdata["data"]["grand_company"]:
            gcpath = "data/ffxiv/images/" + cdata["data"]["grand_company"]["rank"].replace(" ", "_") + ".png"
            if not os.path.exists(gcpath):
                async with aiohttp.get(cdata["data"]["grand_company"]["icon"]) as r:
                    gcimg = await r.content.read()
                with open(gcpath, "wb") as f:
                    f.write(gcimg)
            gc_image = Image.open(gcpath).convert("RGBA")
            process.paste(gc_image, (312, 35))

        # job levels
        jl = {}
        for job in cdata["data"]["classjobs"].keys():
            jl[cdata["data"]["classjobs"][job]["data"]["name"].lower().replace(" ", "")] = \
                cdata["data"]["classjobs"][job]["level"]

        # job icons
        icon_pos = [16, 192]
        for c in ["gladiator", "pugilist", "marauder", "lancer", "archer", "rogue", "conjurer", "thaumaturge",
                  "arcanist", "darkknight", "astrologian", "machinist", "samurai", "redmage"]:
            if c in jl.keys() and jl[c] > 0:
                process.paste(Image.open("data/ffxiv/images/{}.png".format(c)).convert("RGBA"), tuple(icon_pos))
            icon_pos[0] += 26
        icon_pos = [46, 240]
        for c in ["carpenter", "blacksmith", "armorer", "goldsmith", "leatherworker", "weaver", "alchemist",
                  "culinarian", "miner", "botanist", "fisher"]:
            if jl[c] > 0:
                process.paste(Image.open("data/ffxiv/images/{}.png".format(c)).convert("RGBA"), tuple(icon_pos))
            icon_pos[0] += 28

        result = Image.alpha_composite(result, process)

        draw = ImageDraw.Draw(result)
        # TEXT AFTER THIS
        # name, title
        name_color = (0, 0, 0, 255)
        black_color = (0, 0, 0, 255)
        charname = cdata["name"]
        if not cdata["data"]["title"]:
            _write_text(cdata["name"], 110, 36 if len(charname) < 15 else (38 if len(charname) < 18 else 39),
                        name_fnt if len(charname) < 15 else (
                            name_small_fnt if len(charname) < 18 else name_verysmall_fnt), name_color)
        else:
            _write_text(cdata["name"], 110, 28 if len(charname) < 15 else (30 if len(charname) < 18 else 31),
                        name_fnt if len(charname) < 15 else (
                            name_small_fnt if len(charname) < 18 else name_verysmall_fnt), name_color)
            _write_text(cdata["data"]["title"], 130, 56, title_fnt, name_color)

        # Job levels
        text_pos = [17, 216]
        for c in ["gladiator", "pugilist", "marauder", "lancer", "archer", "rogue", "conjurer", "thaumaturge",
                  "arcanist", "darkknight", "astrologian", "machinist", "samurai", "redmage"]:
            if c in jl.keys() and jl[c] > 0:
                _center_text(str(jl[c]), text_pos[0], text_pos[1], 26, 16, level_fnt, black_color)
            text_pos[0] += 26
        text_pos = [46, 264]
        for c in ["carpenter", "blacksmith", "armorer", "goldsmith", "leatherworker", "weaver", "alchemist",
                  "culinarian", "miner", "botanist", "fisher"]:
            if jl[c] > 0:
                _center_text(str(jl[c]), text_pos[0], text_pos[1], 28, 12, level_fnt, black_color)
            text_pos[0] += 28

        # Current job
        _right_text("LEVEL " + str(cdata["data"]["active_class"]["progress"]["level"]) + " " +
                    cdata["data"]["active_class"]["role"]["name"].upper(), 307, 95, current_level_fnt, black_color)

        # minions, mounts
        mpc = [str(cdata["extras"]["mounts"]["obtained"]), str(cdata["extras"]["mounts"]["total"]),
               str(cdata["extras"]["minions"]["obtained"]), str(cdata["extras"]["minions"]["total"])]
        _right_text("Mounts ", 205, 139, minion_fnt, black_color)
        _right_text("Minions ", 205, 163, minion_fnt, black_color)
        _center_text(mpc[0] + " / " + mpc[1], 210, 139, 100, 16, minionamt_fnt, (255, 255, 255, 255))
        _center_text(mpc[2] + " / " + mpc[3], 210, 163, 100, 16, minionamt_fnt, (255, 255, 255, 255))

        # lodestone id
        _right_text("Lodestone ID: " + str(cdata["lodestone_id"]), 344, 16, id_fnt, black_color)

        # server
        _write_text(cdata["server"] + " ({})".format(self.getDC(cdata["server"])), 95, 15, server_fnt, black_color)

        # race
        _center_text(cdata["data"]["race"], 6, 104, 87, 15, race_fnt, black_color)
        _center_text(cdata["data"]["clan"].split(" ")[0], 6, 120, 87, 15, race_fnt, black_color)

        # END
        result.save("data/ffxiv/profiles/{}.png".format(uid), "PNG", quality=100)

        try:
            os.remove("data/ffxiv/profiles/{}.tmp.png".format(uid))
        except:
            pass

    async def draw_recipe(self, rdata):
        title_fnt = ImageFont.truetype(font_bold_file, 16)
        level_fnt = ImageFont.truetype(font_file, 12)
        itemamt_fnt = ImageFont.truetype(font_bold_file, 24)
        itemname_fnt = ImageFont.truetype(font_file, 13)
        id_fnt = ImageFont.truetype(font_file, 10)
        mb_fnt = ImageFont.truetype(font_file, 12)

        level_color = (166, 147, 124, 255)
        qcolors = {"common": (255, 255, 255, 255), "uncommon": (36, 173, 85, 255), "rare": (70, 132, 183, 255),
                   "relic": (110, 67, 133, 255), "aetherial": (232, 131, 141, 255)}

        def _write_text(text, init_x, y, font, fill):
            write_pos = init_x
            for char in text:
                draw.text((write_pos, y), char, font=font, fill=fill)
                write_pos += font.getsize(char)[0]
            return write_pos

        def _right_text(text, max_x, init_y, font, fill):
            w = 0
            for char in text:
                w += font.getsize(char)[0]
            return _write_text(text, max_x - w, init_y, font, fill) - w

        def _fit_text(text, width, font):
            tw = 0
            for char in text:
                tw += font.getsize(char)[0]
            if tw <= width:
                return [text]
            retn = []
            if not " " in text:
                done = False
                i = 0
                while not done:
                    w = 0
                    line = ""
                    while w + font.getsize(text[i])[0] <= width and not done:
                        line += text[i]
                        w += font.getsize(text[i])[0]
                        i += 1
                        if i == len(text):
                            done = True
                            break
                    retn.append(line)
                return retn
            else:
                words = text.split(" ")
                done = False
                i = 0
                while not done:
                    w = 0
                    line = ""
                    while w + font.getsize(words[i])[0] <= width and not done:
                        line += words[i] + " "
                        w += font.getsize(words[i] + " ")[0]
                        i += 1
                        if i == len(words):
                            done = True
                            break
                    retn.append(line)
                return retn

        process = Image.new("RGBA", (400, 300), (255, 255, 255, 0))
        result = Image.new("RGBA", (400, 300), (255, 255, 255, 0))
        result.paste(Image.open("data/ffxiv/recipebg.png").convert("RGBA"), (0, 0))
        draw = ImageDraw.Draw(process)
        border_image = Image.open("data/ffxiv/images/border.png").convert("RGBA")

        # ids
        _right_text("Item ID: {} - Recipe ID: {}".format(rdata["item"]["id"], rdata["id"]), 388, 8, id_fnt,
                    (200, 200, 200, 255))

        # Item name
        _write_text(rdata["item"]["name"], 60, 25, title_fnt, qcolors[rdata["color"]])

        # quantity
        if rdata["craft_quantity"] != 1:
            _write_text("x{}".format(rdata["craft_quantity"]), 52, 51, mb_fnt, (255, 255, 255, 255))

        # Item icon
        async with aiohttp.get(rdata["item"]["icon"]) as r:
            itemicon = await r.content.read()
        with open("data/ffxiv/{}.tmp0.jpg".format(rdata["id"]), "wb") as f:
            f.write(itemicon)
        process.paste(Image.alpha_composite(
            Image.open("data/ffxiv/{}.tmp0.jpg".format(rdata["id"])).convert("RGBA").resize((40, 40), Image.ANTIALIAS),
            border_image), (16, 14))

        # class
        process.paste(Image.open("data/ffxiv/images/{}_2.png".format(rdata["classjob"]["icon"])).convert("RGBA"),
                      (6, 66))
        lvtext = "Level {} ".format(rdata["level_view"])
        _write_text(lvtext, 38, 70, level_fnt, level_color)
        if rdata["stars"] > 0:
            starpos = 38 + level_fnt.getsize(lvtext)[0]
            stimage = Image.open("data/ffxiv/images/recipe_star.png").convert("RGBA")
            for i in range(rdata["stars"]):
                process.paste(stimage, (starpos, 70))
                starpos += 13

        # materials
        num_mat = 0
        num_crys = 0
        for i in range(len(rdata["tree"])):
            imgpos = None
            if rdata["tree"][i]["category_name"] == "Crystal":
                imgpos = (41 + 99 * num_crys, 94)
                textpos = (36 + 99 * num_crys, 100)
                _right_text(str(rdata["tree"][i]["quantity"]), textpos[0], textpos[1], itemamt_fnt,
                            (255, 255, 255, 255))
                num_crys += 1
            else:
                imgpos = (41 if num_mat < 3 else 229, 163 + 45 * (num_mat % 3))
                textpos = (36 if num_mat < 3 else 224, 169 + 45 * (num_mat % 3))
                namepos = (85 if num_mat < 3 else 274, 175 + 45 * (num_mat % 3))
                _right_text(str(rdata["tree"][i]["quantity"]), textpos[0], textpos[1], itemamt_fnt,
                            (255, 255, 255, 255))
                namelines = _fit_text(rdata["tree"][i]["name"], 100, itemname_fnt)
                k = 0
                for line in namelines:
                    _write_text(line, namepos[0], namepos[1] - (len(namelines) - 1) * 7 + 14 * k, itemname_fnt,
                                qcolors[rdata["tree"][i]["color"]])
                    k += 1
                num_mat += 1
            async with aiohttp.get(rdata["tree"][i]["icon"]) as r:
                imgicon = await r.content.read()
            with open("data/ffxiv/{}.tmp{}.jpg".format(rdata["id"], i + 1), "wb") as f:
                f.write(imgicon)
            process.paste(Image.alpha_composite(
                Image.open("data/ffxiv/{}.tmp{}.jpg".format(rdata["id"], i + 1)).convert("RGBA").resize((40, 40),
                                                                                                        Image.ANTIALIAS),
                border_image), imgpos)
        if num_crys == 1:
            process.paste(border_image, (140, 94))
        if num_mat < 6:
            for i in range(num_mat, 6):
                process.paste(border_image, (41 if i < 3 else 229, 163 + 45 * (i % 3)))

        ypos = 70
        # Spec
        if rdata["is_specialization_required"] == 1:
            _right_text("Specialist Recipe", 390, ypos, level_fnt, level_color)
            ypos += 14

        # required stats
        if rdata["required_control"] > 0:
            _right_text("Minimum Control: {}".format(rdata["required_control"]), 390, ypos, level_fnt, level_color)
            ypos += 14
        if rdata["required_craftsmanship"] > 0:
            _right_text("Minimum Craftsmanship: {}".format(rdata["required_craftsmanship"]), 390, ypos, level_fnt,
                        level_color)
            ypos += 14

        # Element
        if rdata["element_name"] != "Aspect: None":
            _right_text(rdata["element_name"], 390, ypos, level_fnt, level_color)
            ypos += 14

        # QS
        if rdata["can_quick_synth"] == 0:
            _right_text("Quick Synthesis unavailable", 390, ypos, level_fnt, level_color)
            ypos += 14

        # master book
        if rdata["masterbook"]:
            _right_text(rdata["masterbook"]["name"], 388, 50, mb_fnt, (255, 255, 255, 255))

        result = Image.alpha_composite(result, process)
        result.save("data/ffxiv/{}.tmp.png".format(rdata["id"]), "PNG", quality=100)

        for i in range(1 + num_mat + num_crys):
            try:
                os.remove("data/ffxiv/{}.tmp{}.jpg".format(rdata["id"], i))
            except:
                pass

    @commands.group(invoke_without_command=True)
    async def fflogs(self, ctx):
        """Display FFlogs rankings and parse infos."""
        if not ctx.invoked_subcommand:
            return

    def getregion(self, server):
        for r in self.fflogs_data["regions"].keys():
            if server.title() in self.fflogs_data["regions"][r]:
                return r
        return ""

    def formatcleartime(ms: int):
        return str(ms // 60000) + ":" + str(round((ms % 60000) / 1000))

    async def _fflogs(self, request, args=None):
        url = "http://www.fflogs.com/v1/" + request + "?api_key=" + self.fflogs_settings["api_key"]
        if args is not None and len(args) > 0:
            for a in args.keys():
                url += "&" + str(a) + "=" + str(args[a])
        async with aiohttp.get(url) as r:
            try:
                d = await r.json()
                return d
            except:
                return {"__ERROR__": "Invalid JSON or no response."}

    @fflogs.command()
    async def setkey(self, ctx, key):
        """Sets which API key the bot should use for getting FFlogs info (provide the public key)."""
        if not self.bot.is_owner(ctx.author):
            return

        if key == "":
            await self.embed(ctx, "FFlogs Info: Error", "API key cannot be empty.", "red")
            return
        self.fflogs_settings["api_key"] = key
        self.save_fflogs_settings()
        await self.embed(ctx, "FFlogs Info", "API key successfully set.", "green")

    async def fflogs_chardata(self, ctx, *, charid=-1, fn="", ln="", sn="", args=None):
        if self.fflogs_settings["api_key"] == "":
            await self.embed(ctx, "FFlogs Info: Error",
                             "No API key set. The bot owner needs to set an API key with `{}fflogs setkey <key>`.".format(
                                 "[p]"), "red")
            return
        embedtext = ""
        charinfo = {}
        req = ""
        if charid != -1:
            charinfo = await self._xivdb("character", id_=charid)
            req = "rankings/character/" + charinfo["name"].replace(" ", "+") + "/" + charinfo[
                "server"] + "/" + self.getregion(charinfo["server"])
            if "error" in charinfo.keys():
                await self.embed(ctx, "FFlogs Info: XIVDB Error", charinfo["error"], "red")
                return
        elif not (fn == "" or ln == "" or sn == ""):
            req = "rankings/character/" + fn.title() + "+" + ln.title() + "/" + sn.title() + "/" + self.getregion(
                sn.title())
        if args is None or args == {}:
            anydata = False
            for group in self.fflogs_data["default_groups"]:
                header2 = False
                if "id" in self.fflogs_data["groups"][group].keys():
                    args = {"zone": self.fflogs_data["groups"][group]["id"]}
                    logdata = await self._fflogs(req, args)
                    if type(logdata) == dict and "status" in logdata.keys() and "error" in logdata.keys():
                        await self.embed(ctx, "FFlogs Info: Error " + logdata["status"], logdata["error"], "red")
                        return
                    if len(logdata) == 0:
                        continue
                    for z in self.fflogs_data["zones"].keys():
                        header = False
                        for enc in logdata:
                            if enc["encounter"] == self.fflogs_data["zones"][z]["id"]:
                                anydata = True
                                if not header2:
                                    embedtext += "__**" + self.fflogs_data["groups"][group]["display"] + "**__\n"
                                    header2 = True
                                if not header:
                                    embedtext += "  **" + self.fflogs_data["zones"][z]["display"] + "**:\n"
                                    header = True
                                embedtext += "    *" + self.fflogs_data["classes"][str(enc["spec"])] + "*: " + str(
                                    round((1 - enc["rank"] / enc["outOf"]) * 100)) + "% (" + str(
                                    enc["rank"]) + "/" + str(enc["outOf"]) + ") - " + str(enc["total"]) + " DPS\n"
                embedtext += "\n"
            if not anydata:
                await self.embed(ctx, "FFlogs Info", "That character has no rankings.", "red")
                return
        await self.embed(ctx, "FFlogs Info for " + (
            fn.title() + " " + ln.title() if fn + ln != "" else charinfo["name"]) + " (" + (
                             sn.title() if sn != "" else charinfo["server"]) + ")", embedtext, "green")

    @fflogs.command()
    async def me(self, ctx, *, options=""):
        """Gets current FFlogs rankings for the character you've saved with [p]ffxiv iam."""
        if not str(ctx.message.author.id) in self.settings["characters"].keys():
            await self.embed(ctx, "FFlogs Info",
                             "No character saved. Please use `[p]ffxiv iam` to save your character.", "red")
            return
        await self.fflogs_chardata(ctx, charid=self.settings["characters"][ctx.message.author.id]["id"])

    @fflogs.command()
    async def char(self, ctx, server, firstname, lastname, *, options=""):
        """Gets current FFlogs rankings for the specified character."""
        if self.fflogs_settings["api_key"] == "":
            await self.embed(ctx, "FFlogs Info: Error",
                             "No API key set. The bot owner needs to set an API key with `{}fflogs setkey <key>`.".format(
                                 "[p]"), "red")
            return
        if self.getregion(server) == "":
            await self.embed(ctx, "FFlogs Info: Error", "No server with that name exists.", "red")
            return
        await self.fflogs_chardata(ctx, fn=firstname, ln=lastname, sn=server)

        # def parseoptions(self, string):
        #     args = {}


        # @fflogs.command(pass_context=True)
        # async def listoptions(self, ctx):
        #     embedtext = """**Supported options to be appended:**
        #
        #     **fight**: Specifies the fight to pull a ranking from
        #     **class**: Only show rankings of this class
        #     **group**: Show rankings from the specified group. Get a list with `[p]fflogs listfights`
        #
        #     Options are passed as key:value and separated by commata, e.g.
        #     `fight:Exdeath,class:Warrior`"""
        #     await self.embed(ctx, "FFlogs Info", embedtext, "purple")


def setup(bot):
    if not os.path.exists("data/ffxiv"):
        print("Creating data/ffxiv folder")
        os.makedirs("data/ffxiv")
    if not os.path.exists("data/ffxiv/profiles"):
        print("Creating data/ffxiv/profiles folder")
        os.makedirs("data/ffxiv/profiles")
    if not os.path.exists("data/ffxiv/images"):
        print("Creating data/ffxiv/images folder")
        os.makedirs("data/ffxiv/images")
    if not os.path.exists("data/ffxiv/settings.json"):
        print("Creating data/ffxiv/settings.json file...")
        dataIO.save_json("data/ffxiv/settings.json", {})
    if not os.path.exists("data/ffxiv/fflogs/settings.json"):
        print("Creating data/ffxiv/fflogs/settings.json file...")
        dataIO.save_json("data/ffxiv/fflogs/settings.json", {"api_key": ""})
    bot.add_cog(FFXIV(bot))
