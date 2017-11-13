import asyncio
from os.path import join
import validators
import discord
import youtube_dl
from discord.ext import commands
import aiohttp
import re
import urllib
import json as simplejson


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
ytdl.params["outtmpl"] = join("music", ytdl.params["outtmpl"])



class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, ytdl.extract_info, url)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                   data=data)


class Music:
    def __init__(self, bot):
        self.bot = bot
        self.youtube_regex = (
          r'(https?://)?(www\.)?'
          '(youtube|youtu|youtube-nocookie)\.(com|be)/'
          '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')

    @commands.command()
    async def queue(self, ctx, *, searchurl):
        """Streams from a url (almost anything youtube_dl supports)"""
       
        def check(r, user):
            if user != ctx.message.author:
                return False
            reactionlist = ['0\u20e3','1\u20e3','2\u20e3','3\u20e3','4\u20e3']
            if r.emoji not in reactionlist:
                return False
            else:

                return True

        if not validators.url(searchurl):
            try:
                url = 'https://www.youtube.com/results?'
                payload = {'search_query': ''.join(searchurl)}
                headers = {'user-agent': 'Red-cog/1.0'}
                conn = aiohttp.TCPConnector()
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    result = await r.text()
                session.close()
                yt_find = re.findall(r'href=\"\/watch\?v=(.{11})', result)
                yt_find = list(set(yt_find))
                
                results = 'Options are\n'
                for x in range(0,5):
                    api_key = 'AIzaSyB10j5t3LxMpuedlExxcVvj0rsezTurY9w'
                    gurl = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id="+yt_find[x*2]+"&key="+api_key+"&part=contentDetails"
                    json = simplejson.loads(urllib.request.urlopen(gurl).read())
                    results += str(x)+'\u20e3' + ": " + json['items'][0]['snippet']['title'] + '\n'

                sentmessage = await ctx.send(results)

                await sentmessage.add_reaction('0\u20e3')
                await sentmessage.add_reaction('1\u20e3')
                await sentmessage.add_reaction('2\u20e3')
                await sentmessage.add_reaction('3\u20e3')
                await sentmessage.add_reaction('4\u20e3')
                print('before wait for')
                choice = await self.bot.wait_for('reaction_add', check = check, timeout = 30.0)
                chosen = ''
                print(choice[0].emoji)               
                if choice[0].emoji == '0\u20e3':
                    chosen = 0  
                elif choice[0].emoji =='1\u20e3':
                    chosen = 1
                elif choice[0].emoji =='2\u20e3':
                    chosen = 2
                elif choice[0].emoji =='3\u20e3':
                    chosen = 3
                elif choice[0].emoji =='4\u20e3':
                    chosen = 4
                else:
                    print("Something broke in audio")
                    return

                
                searchurl = 'https://www.youtube.com/watch?v={}'.format(yt_find[chosen])
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
                await ctx.send(message)
        query =  "INSERT INTO music_queues (guildid, songurl) VALUES ($1, $2)"
        await ctx.db.execute(query, ctx.guild.id, searchurl)
        await ctx.send("Added to queue: " + searchurl)
    
    @commands.command()
    async def play(self, ctx, *, searchurl=None):
        """Streams from a url (almost anything youtube_dl supports)"""

        def play_next(error):
            coro = self.play(ctx)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            fut.result()
            

        if ctx.voice_client is None:
            if (ctx.author.voice is not None) and (ctx.author.voice.channel is not None):
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send("Not connected to a voice channel.")

        if(searchurl == None):
            query = "SELECT * FROM music_queues WHERE guildid = $1"
            queue = await ctx.db.fetch(query,ctx.guild.id)
            searchurl = queue[0]['songurl']
            id = queue[0]['id']
            player = await YTDLSource.from_url(searchurl, loop=self.bot.loop)
            ctx.voice_client.play(player, after=play_next)
            query = "DELETE FROM music_queues WHERE id = $1"
            await ctx.db.execute(query, id)
            return

        
        def check(r, user):
            if user != ctx.message.author:
                return False
            reactionlist = ['0\u20e3','1\u20e3','2\u20e3','3\u20e3','4\u20e3']
            if r.emoji not in reactionlist:
                return False
            else:

                return True

        if not validators.url(searchurl):
            try:
                url = 'https://www.youtube.com/results?'
                payload = {'search_query': ''.join(searchurl)}
                headers = {'user-agent': 'Red-cog/1.0'}
                conn = aiohttp.TCPConnector()
                session = aiohttp.ClientSession(connector=conn)
                async with session.get(url, params=payload, headers=headers) as r:
                    result = await r.text()
                session.close()
                yt_find = re.findall(r'href=\"\/watch\?v=(.{11})', result)
                yt_find = list(set(yt_find))
                
                results = 'Options are\n'
                for x in range(0,5):
                    api_key = 'AIzaSyB10j5t3LxMpuedlExxcVvj0rsezTurY9w'
                    gurl = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id="+yt_find[x*2]+"&key="+api_key+"&part=contentDetails"
                    json = simplejson.loads(urllib.request.urlopen(gurl).read())
                    results += str(x)+'\u20e3' + ": " + json['items'][0]['snippet']['title'] + '\n'

                sentmessage = await ctx.send(results)

                await sentmessage.add_reaction('0\u20e3')
                await sentmessage.add_reaction('1\u20e3')
                await sentmessage.add_reaction('2\u20e3')
                await sentmessage.add_reaction('3\u20e3')
                await sentmessage.add_reaction('4\u20e3')
                print('before wait for')
                choice = await self.bot.wait_for('reaction_add', check = check, timeout = 30.0)
                chosen = ''
                print(choice[0].emoji)               
                if choice[0].emoji == '0\u20e3':
                    chosen = 0  
                elif choice[0].emoji =='1\u20e3':
                    chosen = 1
                elif choice[0].emoji =='2\u20e3':
                    chosen = 2
                elif choice[0].emoji =='3\u20e3':
                    chosen = 3
                elif choice[0].emoji =='4\u20e3':
                    chosen = 4
                else:
                    print("Something broke in audio")
                    return


                searchurl = 'https://www.youtube.com/watch?v={}'.format(yt_find[chosen*2])
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
                await ctx.send(message)

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        player = await YTDLSource.from_url(searchurl, loop=self.bot.loop)
        ctx.voice_client.play(player, after=play_next)

        await ctx.send('Now playing: {}'.format(player.title))



    @commands.command()
    async def volume(self, ctx, volume: float):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()


def setup(bot):
    bot.add_cog(Music(bot))