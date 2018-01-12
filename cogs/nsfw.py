import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import random
from .utils import checks
import aiohttp
import requests
import urllib
import json
import math
import asyncio

class Nsfw:
    """Nsfw commands."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.tasks = []


    @commands.command()
    @checks.is_nsfw()
    async def dick(self, ctx, user : discord.Member):
        """Show's the size of the user's dick (157% accurate)"""

        random.seed(int(user.id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 15)
        y = "=" *  x
        await ctx.send("{}\'s dick:' ** 8{}D **".format(user.name, y))

    @commands.command()
    @checks.is_nsfw()
    async def boobs(self, ctx, user : discord.Member):
        """Shows the size of the user's boobs (157% accurate)"""

        random.seed(int(user.id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 5)
        y = " " *  x
        await ctx.send("{}\'s boobs:' ** ( .{}Y{}. ) **".format(user.name, y, y))

    @commands.command()
    @checks.is_nsfw()
    async def ass(self, ctx, user : discord.Member):
        """Shows the size of the user's ass (157% accurate)"""

        random.seed(int(user.id) % int(ctx.message.created_at.timestamp()),)
        x = random.randint(1, 5)
        y = " " *  x
        await ctx.send("{}\'s ass:' ** ({}!{}) **".format(user.name, y, y))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def yandere(self, ctx):
        """Random Image From Yandere"""
        try:
            query = ("https://yande.re/post/random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="highres").get("href")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def konachan(self, ctx):
        """Random Image From Konachan"""
        try:
            query = ("https://konachan.com/post/random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="highres").get("href")
            await ctx.send('https:' + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def rule34(self, ctx):
        """Random Image From rule34"""
        try:
            query = ("https://rule34.xxx/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send('http:' + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def gelbooru(self, ctx):
        """Random Image From Gelbooru"""
        try:
            query = ("https://www.gelbooru.com/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def tbib(self, ctx):
        """Random Image From DrunkenPumken"""
        try:
            query = ("https://www.tbib.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send("http:" + image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def xbooru(self, ctx):
        """Random Image From Xbooru"""
        try:
            query = ("https://xbooru.com/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            await ctx.send(image)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def furrybooru(self, ctx):
        """Random Image From Furrybooru"""
        try:
            query = ("http://furry.booru.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            head, sep, tail = image.partition('?')
            clean = head.replace("//","/").replace("http:/", "http://")
            em = discord.Embed(color=ctx.message.author.color, description=" ")
            em.set_author(name="Random Image from Furrybooru:", icon_url="http://bit.ly/2hHIfF6")
            em.set_image(url=clean)
            em.set_footer(text= "Random image from http://furry.booru.org")
            await ctx.send(embed=em)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def drunkenpumken(self, ctx):
        """Random Image From DrunkenPumken"""
        try:
            query = ("http://drunkenpumken.booru.org/index.php?page=post&s=random")
            page = await self.session.get(query)
            page = await page.text()
            soup = BeautifulSoup(page, 'html.parser')
            image = soup.find(id="image").get("src")
            head, sep, tail = image.partition('?')
            clean = head.replace("//","/").replace("http:/", "http://")
            em = discord.Embed(color=ctx.message.author.color, description=" ")
            em.set_author(name="Random Image from DrunkenPumken:", icon_url="http://bit.ly/2hHIfF6")
            em.set_image(url=clean)
            em.set_footer(text= "Random image from http://drunkenpumken.booru.org")
            await ctx.send(embed=em)
        except Exception as e:
            await ctx.send(":x: **Error:** `{}`".format(e))

    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def gayorzea(self, ctx):
       """Random image from gayorzea.com coming soon"""


    @commands.command()
    @commands.guild_only()
    @checks.is_nsfw()
    async def ysearch(self, ctx, *tags: str):
        """Search Yandere With A Tag"""
        if tags == ():
            await ctx.send(":warning: Tags are missing.")
        else:
            try:
                tags = ("+").join(tags)
                query = ("https://yande.re/post.json?limit=42&tags=" + tags)
                page = await self.session.get(query)
                json = await page.json()
                if json != []:
                    em = discord.Embed(color=ctx.message.author.color, description=" ")
                    em.set_author(name="Yandere image search:", icon_url="http://bit.ly/2hHIfF6")
                    em.set_image(url=random.choice(json)['jpeg_url'])
                    em.set_footer(text= "Image of"+ tags +"from https://yande.re/")
                    await ctx.send(embed=em)
                else:
                    await ctx.send(":warning: Yande.re has no images for requested tags.")
            except Exception as e:
                await ctx.send(":x: `{}`".format(e))

    # Gets videos using the Hub Traffic API
    def getVidsAPI(self, url, actualPage, skip, rating, stillNeed):
        fullUrl = url + '&page=' + str(actualPage)
        print(fullUrl)

        r = requests.get(fullUrl)
        if r.status_code != 200:
            print('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            # await ctx.send('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            return []

        rJson = json.loads(r.text)

        if ("videos" in rJson):
            vidJson = rJson["videos"]
        else:
            # No videos!
            return []

        # Find video URLs and Titles
        vids = []

        i = 0
        while i < len(vidJson) and stillNeed > 0:
            key = vidJson[i]["video_id"]
            # print(key)

            title = vidJson[i]["title"]
            # print(title)

            dur = vidJson[i]["duration"]
            # print(dur)

            views = vidJson[i]["views"]
            views = "{:,}".format(int(views))
            # print(views)

            rate = str(int(round(float(vidJson[i]["rating"]))))
            # print(rate)

            if int(rate) >= rating:
                if skip > 0:
                    skip -= 1
                else:
                    vids.append([key, title, dur, views, rate])
                    stillNeed -= 1

            i += 1

        if stillNeed > 0:
            vids += self.getVidsAPI(url, actualPage + 1, skip, rating, stillNeed)

        return vids

    # Scrapes videos from webpage HTML
    def getVids(self, url, actualPage, skip, rating, stillNeed):
        fullUrl = url + '&page=' + str(actualPage)
        print(fullUrl)

        r = requests.get(fullUrl)
        if r.status_code != 200:
            print('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            # await ctx.send('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        videoContainer = soup.find("ul", class_="search-video-thumbs")
        vidBoxes = videoContainer.find_all("li", class_="videoblock videoBox")

        # Find video URLs and Titles
        vids = []

        i = 0
        while i < len(vidBoxes) and stillNeed > 0:
            key = vidBoxes[i]['_vkey']
            # print(key)

            title = vidBoxes[i].find('a', class_="img")['title']
            # Replace encoded chars
            title = title.replace("&#039;", "'")
            title = title.replace("&amp;", "&")
            title = title.replace("&quot;", '"')
            title = title.replace("&mdash;", '-')
            # print(title)

            dur = vidBoxes[i].find('var', class_="duration").string
            # print(dur)

            views = vidBoxes[i].find('span', class_="views").var.string
            # print(views)

            rate = vidBoxes[i].find('div', class_="value").string
            rate = rate[0:len(rate)-1]
            # print(rate)

            if int(rate) >= rating:
                if skip > 0:
                    skip -= 1
                else:
                    vids.append([key, title, dur, views, rate])
                    stillNeed -= 1

            i += 1

        if stillNeed > 0:
            vids += self.getVids(url, actualPage + 1, skip, rating, stillNeed)

        return vids

    def getVideo(self, vidID:str):
        fullUrl = "https://www.pornhub.com/webmasters/video_by_id?thumbsize=small&id=" + vidID
        print(fullUrl)

        r = requests.get(fullUrl)
        if r.status_code != 200:
            print('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            # await ctx.send('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            return []

        rJson = json.loads(r.text)

        if "video" in rJson:
            vidJson = rJson["video"]
        else:
            # No video!
            return []

        # Find video Info
        key = vidJson["video_id"]
        # print(key)

        title = vidJson["title"]
        # print(title)

        dur = vidJson["duration"]
        # print(dur)

        views = vidJson["views"]
        views = "{:,}".format(int(views))
        # print(views)

        rate = str(int(round(float(vidJson["rating"]))))
        # print(rate)

        cats = []
        for i in range(len(vidJson["categories"])):
            cats.append(vidJson["categories"][i]["category"].replace("-", " ").title())
        # print(cats)

        tags = []
        for i in range(len(vidJson["tags"])):
            tags.append(vidJson["tags"][i]["tag_name"])
        # print(tags)

        ps = []
        for i in range(len(vidJson["pornstars"])):
            ps.append(vidJson["pornstars"][i]["pornstar_name"])
        # print(ps)

        thumb = vidJson["default_thumb"]
        # print(thumb)

        vid = [key, title, dur, views, rate, cats, tags, ps, thumb]

        return vid

    async def printVids(self, ctx, vids, query, page, rating):
        if len(vids) <= 0:
            await ctx.send("No videos found :cry:")
        else:
            resEmbed = discord.Embed(title='__Choose one by giving its number__', colour=discord.Colour(0xFF9900))
            resEmbed.set_footer(text=query + ' Results - Page ' + str(page))
            for i in range(len(vids)):
                goodBad = 'Rating:' if int(vids[i][4]) >= 50 else 'Rating:'
                pornTitle = str(i + page * 5 - 4) + '. ' + vids[i][1]
                pornStats = '\tDuration ' + vids[i][2] + '\tViews ' + vids[i][3] + '\t' + goodBad + ' ' + vids[i][4] + '%'
                resEmbed.add_field(name=pornTitle, value=pornStats, inline=False)

            await ctx.send(embed=resEmbed)

            def check(m):
                if m.author != ctx.message.author:
                    return False
                if m.channel != ctx.message.channel:
                    return False
                return m.content in map(str, range(page * 5 - 4, page * 5 - 4 + len(vids)))

            # Append it so it can be cancelled later if needed
            self.tasks.append(asyncio.ensure_future(self.bot.wait_for('message', check=check,timeout=20)))
            resp = await self.tasks[len(self.tasks)-1]

            selectedVidIndex = (int(resp.content) - 1) % 5
            selectedVid = self.getVideo(vids[selectedVidIndex][0])

            # Video data didn't come back for so
            await ctx.send("Error getting your video :cry:")
            return

            goodBad = 'Rating:' if int(selectedVid[4]) >= 50 else 'Rating:'
            vidUrl = 'https://www.pornhub.com/view_video.php?viewkey=' + selectedVid[0]
            vidStats = '\tDuration: ' + selectedVid[2] + '\tViews: ' + selectedVid[3] + '\t' + goodBad + ' ' + selectedVid[4] + '%'
            catString = ", ".join(selectedVid[5])
            tagString = ", ".join(selectedVid[6])

            vidEmbed = discord.Embed(title="__"+selectedVid[1]+"__", colour=discord.Colour(0xFF9900))
            vidEmbed.set_image(url=selectedVid[8])
            vidEmbed.add_field(name="Stats", value=vidStats, inline=False)
            vidEmbed.add_field(name="URL", value=vidUrl, inline=False)

            await ctx.send(embed=vidEmbed)


    @commands.command()
    @checks.is_nsfw()
    async def pornhub(self, ctx,  query, page: int, rating: int):
        """Search Pornhub for porn."""
        if query.lower() == "help":
            helpEmbed = discord.Embed(title="*.pornhub search <query> [page] [minRating]*", colour=discord.Colour(0xFF9900))
            helpEmbed.set_author(name="PornHub Search Help")
            helpEmbed.add_field(name="Description",
                                value="Allows you to search PornHub for videos. Simple as that!",
                                inline=False)
            helpEmbed.add_field(name="Arguments",
                                value="**query:** What you want to search for\n"
                                      "**page:** What page of results you want to go to (default=1)\n"
                                      "**minRating:** Must be an integer between 0 and 100. Videos with a rating lower than this number won't be displayed in results (default=0)",
                                inline=False)
            await ctx.send(embed=helpEmbed)
            return

        if rating < 0 or rating > 100: rating = 0
        if page <= 0: page = 1

        # Call the API
        # Start at page 1 if rating is something other than 0
        actualPage = 1 if rating != 0 else math.ceil(page / 6)
        skip = 5 * ((page - 1) % 6)
        # print(query)
        baseUrl = "http://www.pornhub.com/webmasters/search?thumbsize=medium&search="
        parsedQuery = urllib.parse.quote_plus(query)
        partialUrl = baseUrl + parsedQuery
        vids = self.getVidsAPI(partialUrl, actualPage, skip, rating, 5)


        # --- BACKUP HTML SCRAPER METHOD ---
        # Start at page 1 if rating is something other than 0
        # actualPage = 1 if rating != 0 else math.ceil(page / 4)
        # skip = 5 * ((page - 1) % 4)
        # print(query)
        # baseUrl = "https://www.pornhub.com/video/search?search="
        # parsedQuery = urllib.parse.quote_plus(query)
        # partialUrl = baseUrl + parsedQuery
        # vids = self.getVids(partialUrl, actualPage, skip, rating, 5)

        await self.printVids(ctx, vids, query, page, rating)


    @commands.command()
    @checks.is_nsfw()
    async def phtoprated(self,ctx, page: int = 1, rating: int = 0):
        """Get a list of the top rated videos on pornhub"""
        await self.toprated_func(ctx,page, rating)

    async def toprated_func(self, ctx, page, rating):
        if rating < 0 or rating > 100: rating = 0
        if page <= 0: page = 1
        # Start at page 1 if rating is something other than 0
        actualPage = 1 if rating != 0 else math.ceil(page / 4)
        skip = 4 * ((page - 1) % 8)

        baseUrl = "https://www.pornhub.com/video?o=tr"

        vids = self.getVids(baseUrl, actualPage, skip, rating, 4)
        await self.printVids(ctx, vids, "This Week's Top Rated Porn Videos", page, rating)

    @commands.command()
    @checks.is_nsfw()
    async def phhome(self, ctx):
        """Get a list of the videos on the pornhub homepage."""
        url = "https://www.pornhub.com/"
        r = requests.get(url)
        if r.status_code != 200:
            print('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            await ctx.send('Error ' + str(r.status_code) + ': Cannot connect to PornHub.com :cry:')
            return

        soup = BeautifulSoup(r.text, "html.parser")
        videoContainers = soup.find_all("div", class_="sectionWrapper")
        hotVidBoxes = videoContainers[0].find_all("li", class_="videoblock videoBox")
        mvVidBoxes = videoContainers[1].find_all("li", class_="videoblock videoBox")
        vidBoxes = hotVidBoxes + mvVidBoxes

        # Find video URLs and Titles
        vids = []

        # Get Hot Vids and Most Watched Vids
        i = 0
        while i < len(vidBoxes) and len(vids) <= 11:
            tempKey = vidBoxes[i]['_vkey']

            tempTitle = vidBoxes[i].find('a', class_="img")['title']
            # Replace encoded chars
            tempTitle = tempTitle.replace("&#039;", "'")
            tempTitle = tempTitle.replace("&amp;", "&")
            tempTitle = tempTitle.replace("&quot;", '"')
            tempTitle = tempTitle.replace("&mdash;", '-')

            tempDur = vidBoxes[i].find('var', class_="duration").string

            tempViews = vidBoxes[i].find('span', class_="views").var.string

            tempRate = vidBoxes[i].find('div', class_="value").string[0:2]

            vids.append([tempKey, tempTitle, tempDur, tempViews, tempRate])
            # Go to next vid
            i += 1

        hotEmbed = discord.Embed(title='__Hot Porn Videos__', colour=discord.Colour(0xFF9900))
        hotEmbed.set_author(name="**PornHub Home - Choose one by giving its number**")
        hotEmbed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/7/7c/Logo_of_Pornhub.png")
        for i in range(6):
            goodBad = ':thumbsup:' if int(vids[i][4]) >= 50 else ':thumbsdown:'
            pornTitle = str(i + 1) + '. ' + vids[i][1]
            pornStats = '\t:clock2: ' + vids[i][2] + '\t:eyes: ' + vids[i][3] + '\t' + goodBad + ' ' + vids[i][4] + '%'
            hotEmbed.add_field(name=pornTitle, value=pornStats, inline=False)

        await ctx.send(embed=hotEmbed)

        mvEmbed = discord.Embed(title='__Most Viewed Videos__', colour=discord.Colour(0xFF9900))
        for i in range(6, 11):
            goodBad = 'Rating:' if int(vids[i][4]) >= 50 else 'Rating:'
            pornTitle = str(i + 1) + '. ' + vids[i][1]
            pornStats = '\tDuration: ' + vids[i][2] + '\tViews: ' + vids[i][3] + '\t' + goodBad + ' ' + vids[i][4] + '%'
            mvEmbed.add_field(name=pornTitle, value=pornStats, inline=False)

        await ctx.send(embed=mvEmbed)

        def check(m):
            if m.author != ctx.message.author:
                return False
            if m.channel != ctx.message.channel:
                return False
            return m.content in map(str, range(1, 12))

        # Append it so it can be cancelled later if needed
        self.tasks.append(asyncio.ensure_future(self.bot.wait_for('message', check=check, timeout=20)))
        resp = await self.tasks[len(self.tasks) - 1]
        # resp = await self.bot.wait_for_message(author=ctx.message.author, check=check,
        #

        selectedVidIndex = (int(resp.content) - 1)
        selectedVid = self.getVideo(vids[selectedVidIndex][0])

        # Video data didn't come back for some reason?
        if not selectedVid:
            await ctx.send("Error getting your video :cry:")
            return

        goodBad = 'Rating:' if int(selectedVid[4]) >= 50 else 'Rating:'
        vidUrl = 'https://www.pornhub.com/view_video.php?viewkey=' + selectedVid[0]
        vidStats = '\tDuration ' + selectedVid[2] + '\tViews: ' + selectedVid[3] + '\t' + goodBad + ' ' + selectedVid[4] + '%'
        catString = ", ".join(selectedVid[5])
        tagString = ", ".join(selectedVid[6])

        vidEmbed = discord.Embed(title="__" + selectedVid[1] + "__", colour=discord.Colour(0xFF9900))
        vidEmbed.add_field(name="Stats", value=vidStats, inline=False)
        vidEmbed.set_image(url=selectedVid[8])
        vidEmbed.add_field(name="URL", value=vidUrl, inline=False)

        await ctx.send(embed=vidEmbed)

def setup(bot):
    n = Nsfw(bot)
    bot.add_cog(n)