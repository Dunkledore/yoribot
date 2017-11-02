import asyncio
from os.path import join
import validators
import discord
import youtube_dl
from discord.ext import commands
import aiohttp
import re
import urllib2
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

    @commands.command(name="local")
    async def play_file(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        if ctx.voice_client is None:
            if ctx.author.voice.channel:
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send("Not connected to a voice channel.")

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print(
            'Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(query))

    @commands.command()
    async def play(self, ctx, *, searchurl):
        """Streams from a url (almost anything youtube_dl supports)"""

        if ctx.voice_client is None:
            if (ctx.author.voice is not None) and (ctx.author.voice.channel is not None):
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send("Not connected to a voice channel.")

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
                
                results = ''
                for x in range(0,5):
                    api_key = 'AIzaSyB10j5t3LxMpuedlExxcVvj0rsezTurY9w'
                    gurl = "https://www.googleapis.com/youtube/v3/videos?part=snippet&id="+yt_find[x]+"&key="+api_key+"&part=contentDetails"
                    print(gurl)
                    results += simplejson.load(urllib2.urlopen(gurl))['entry']['title']['$t']

                await ctx.send(results)

                searchurl = 'https://www.youtube.com/watch?v={}'.format(yt_find[0])
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
                await ctx.send(message)

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        player = await YTDLSource.from_url(searchurl, loop=self.bot.loop)
        ctx.voice_client.play(player, after=lambda e: print(
            'Player error: %s' % e) if e else None)

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