import discord
import asyncio
from discord import option
import yt_dlp as youtube_dl
from discord.ext import commands


q = {}
loop = {}
repeat = {}
pause = {}
secs = {}
task = {}
vstate = {}


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client

    def ytsearch_extract(self, url, guild):
        ydl_opts = {'default_search': 'auto', 'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            try:
                for i in info['entries']:
                    (q[guild]).append(i)
            except KeyError:
                (q[guild]).append(info)


    async def play(self, vstate, guild):
        while len(q[guild]) != 0:
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                              'options': '-vn'}
            playing = q[guild][0]['url']
            vstate.play(discord.FFmpegPCMAudio(playing, **FFMPEG_OPTIONS))
            secs[guild] = q[guild][0]['duration']
            while secs[guild] >= 0:
                await asyncio.sleep(1)
                if not pause[guild]:
                    secs[guild] = secs[guild] - 1
            if not repeat[guild]:
                if loop[guild]:
                    q[guild].append(q[guild][0])
                q[guild].pop(0)



    @commands.slash_command(name='play')
    @option("source", description="play the given source from youtube", required=True)
    async def queue(self, ctx: discord.ApplicationContext, source: str):
        guild = ctx.guild.id
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_connected():
            voice_channel = voice_client.channel
            same = False
            for member in voice_channel.members:
                if member.id == ctx.author.id:
                    same = True
                    break
            if same:
                voice = vstate[guild]
                if len(q[guild]) == 0:
                    self.ytsearch_extract(source, guild)
                    task[guild] = asyncio.create_task(self.play(voice, guild))
                    await ctx.respond("successfully added the track to the queue")
                else:
                    self.ytsearch_extract(source, guild)
                    await ctx.respond("successfully added the track to the queue")
            else:
                voice = vstate[guild]
                await voice.disconnect()
                voice = await ctx.author.voice.channel.connect()
                await ctx.respond("successfully connected the bot to the user's voice channel")
                q[guild] = []
                vstate[guild] = voice
                loop[guild] = False
                pause[guild] = False
                repeat[guild] = False
                self.ytsearch_extract(source, guild)
                task[guild] = asyncio.create_task(self.play(voice, guild))
        else:
            voice = await ctx.author.voice.channel.connect()
            await ctx.respond("successfully connected the bot to the user's voice channel")
            q[guild] = []
            vstate[guild] = voice
            loop[guild] = False
            pause[guild] = False
            repeat[guild] = False
            self.ytsearch_extract(source, guild)
            task[guild] = asyncio.create_task(self.play(voice, guild))

    @commands.slash_command()
    async def queued_tracks(self, ctx: discord.ApplicationContext):
        try:
            if len(q[ctx.guild.id]) != 0:
                index = 0
                for i in q[ctx.guild.id]:
                    index += 1
                    await ctx.respond(f"{index}.{i['webpage_url']}")
            else:
                await ctx.respond("no tracks are currently queued")
        except KeyError:
            await ctx.respond("no queue are created in this guild")

    @commands.slash_command(name='disconnect')
    async def dc(self, ctx: discord.ApplicationContext):
        guild = ctx.guild.id
        if not ctx.voice_client:
            await ctx.respond("the bot is not connected to any voice channel")
        else:
            q[guild] = []
            loop[guild] = False
            repeat[guild] = False
            await vstate[guild].disconnect(force=True)
            task[guild].cancel()
            await ctx.respond("successfully disconnected the bot from the voice channel")

    @commands.slash_command(name='loop')
    async def loop(self, ctx: discord.ApplicationContext):
        guild = ctx.guild.id
        if loop.get(guild) != None:
            if loop[guild]:
                loop[guild] = False
                await ctx.respond("stopped looping")
            else:
                loop[guild] = True
                await ctx.respond("started looping")
        else:
            await ctx.respond("the queue hasn't been created in this guild")

    @commands.slash_command(name='repeat')
    async def repeat(self, ctx: discord.ApplicationContext):
        guild = ctx.guild.id
        if repeat.get(guild) != None:
            if repeat[guild]:
                repeat[guild] = False
                await ctx.respond("stopped looping")
            else:
                repeat[guild] = True
                await ctx.respond("started looping")
        else:
            await ctx.respond("the queue hasn't been created in this guild")

    @commands.slash_command(name='pause_play')
    async def pause_state(self, ctx: discord.ApplicationContext):
        try:
            guild = ctx.guild.id
            voice = vstate[guild]
            if not voice.is_paused():
                voice.pause()
                pause[guild] = True
                await ctx.respond("successfully paused the playback")
            else:
                voice.resume()
                pause[guild] = False
                await ctx.respond("successfully resume the playback")
        except KeyError:
            await ctx.respond("lazy right now not explaining error to u")

    @commands.slash_command(name='remove_from_queue')
    @option("index", description="the index to remove", required=True)
    async def remove(self, ctx: discord.ApplicationContext, index: int):
        try:
            i = int(index)
        except ValueError:
            await ctx.respond('please enter a number')
            return
        guild = ctx.guild.id
        try:
            if len(q[guild]) != 0:
                try:
                    (q[guild]).pop(i - 1)
                    await ctx.respond("successfully removed the track from queue")
                except IndexError:
                    await ctx.respond("no track is in that position of the queue")
            else:
                await ctx.respond('no track is currently queued')
        except KeyError:
            await ctx.respond("lazy right now not explaining error to u")

    @commands.slash_command(name='skip')
    async def skip(self, ctx: discord.ApplicationContext):
        try:
            guild = ctx.guild.id
            voice = vstate[guild]
            voice.stop()
            task[guild].cancel()
            if loop[guild]:
                played = (q[guild])[0]
                (q[guild]).pop(0)
                (q[guild]).append(played)
            else:
                (q[guild]).pop(0)
            voice = vstate[guild]
            task[guild] = asyncio.create_task(self.play(voice, guild))
            await ctx.respond("successfully skipped the track")
        except KeyError:
            await ctx.respond("lazy right now not explaining error to u")


def setup(client):
    client.add_cog(Music(client))
