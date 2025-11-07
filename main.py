####################################################################
#                                                                  #
#    Credit: therealOri  |  https://github.com/therealOri          #
#                                                                  #
####################################################################

####################################################################################
#                                                                                  #
#                            Imports & definitions                                 #
#                                                                                  #
####################################################################################
# Pycord
import asyncio
import discord
import os
import datetime
from libs import rnd
import tomllib
import time
from beaupy.spinners import *
import re
import yt_dlp
from datetime import timedelta
from collections import deque
from typing import Dict, Optional, List

#Load our config for main
with open('config.toml', 'rb') as fileObj:
    config = tomllib.load(fileObj) #dictionary/json




__authors__ = '@therealOri'
token = config["TOKEN"]
bot_logo = config["bot_logo"]
author_logo = None
guild_id = config["guild_id"]


hex_red=0xFF0000
hex_green=0x0AC700
hex_yellow=0xFFF000 # I also like -> 0xf4c50b

# +++++++++++ Imports and definitions +++++++++++ #














####################################################################################
#                                                                                  #
#                             Normal Functions                                     #
#                                                                                  #
####################################################################################
def clear():
    os.system("clear||cls")



def random_hex_color():
    hex_digits = '0123456789abcdef'
    hex_digits = rnd.shuffle(hex_digits)
    color_code = ''
    nums = rnd.randint(0, len(hex_digits)-1, 6)
    for _ in nums:
        color_code += hex_digits[_]
    value =  int(f'0x{color_code}', 16)
    return value


def is_youtube_url(url):
    # Regular expression for YouTube URLs
    # Matches standard youtube.com URLs, youtu.be short URLs, and playlist URLs
    youtube_regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/|playlist\?list=)|youtu\.be/)([\w-]+)(?:\S+)?'

    match = re.match(youtube_regex, url)
    return match is not None

def is_youtube_playlist(url):
    # Check specifically for playlist URLs
    playlist_regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com/playlist\?list=)([\w-]+)(?:\S+)?'
    match = re.match(playlist_regex, url)
    return match is not None



def check_live_url(url: str) -> bool:
    #Youtube only supported right now.
    regex = re.compile(r"https://www\.youtube\.com/live/[A-Za-z0-9]+", re.IGNORECASE)
    result = regex.match(url)
    if result == None:
        return False
    else:
        return True


# +++++++++++ Normal Functions +++++++++++ #













####################################################################################
#                                                                                  #
#                   Async Functions, buttons, modals, etc.                         #
#                                                                                  #
####################################################################################
class MusicQueue:
    """Class to manage the music queue"""

    def __init__(self):
        self.guilds: Dict[int, GuildMusicQueue] = {}

    def get_guild_queue(self, guild_id: int) -> 'GuildMusicQueue':
        """Get a guild's queue, creating it if it doesn't exist."""
        if guild_id not in self.guilds:
            self.guilds[guild_id] = GuildMusicQueue()
        return self.guilds[guild_id]

class GuildMusicQueue:
    """Music queue for a specific guild."""

    def __init__(self):
        self.queue = deque()
        self.current_track = None
        self.voice_client = None
        self.is_playing = False
        self.is_paused = False
        self.processing_playlist = False  # Flag to track if we're processing a playlist
        self.position = 0  # Track position in queue
        self.now_playing_message = None


    def add_playlist(self, playlist_url, requester):
        """Add a playlist URL to the playlist queue."""
        self.playlist_queue.append({"url": playlist_url, "requester": requester})
        return len(self.playlist_queue)

    async def process_next_from_playlist(self, ctx):
        """Process the next track from a playlist if the queue is empty."""
        if self.playlist_queue and not self.processing_playlist:
            self.processing_playlist = True
            playlist_info = self.playlist_queue.popleft()

            # Extract videos from the playlist
            video_urls = await extract_playlist_urls(playlist_info["url"])

            # Process all videos and add them to the queue
            if video_urls:
                await ctx.followup.send(f"✅ Processing {len(video_urls)} songs from playlist...")

                # Add all videos to the main queue
                for url in video_urls:
                    video_info = await get_youtube_info(url, playlist_info["requester"])
                    if video_info:
                        self.add(video_info)

            self.processing_playlist = False
            return True
        return False


    def add(self, url, requester):
        queue_item = {
            'url': url,
            'requester': requester
        }
        self.queue.append(queue_item)
        return len(self.queue)

    def get_next(self):
        if not self.queue:
            return None
        return self.queue.popleft()

    def clear(self):
        self.queue.clear()

    def current_position(self):
        return 0 if self.current_track else -1

    def queue_length(self):
        return len(self.queue)

    def get_queue_list(self):
        return list(self.queue)

    def skip_to(self, position):
        if position <= 0 or position > len(self.queue):
            return False

        # Remove tracks before the desired position
        for _ in range(position - 1):
            self.queue.popleft()
        return True




async def status():
    while True:
        status_messages = ['my internals', '/help for help', 'your navigation history', 'myself walking on the grass', 'Global Global Global', 'base all your 64', 'your security camera footage', 'myself walking on the moon', 'your browser search history']
        smsg = rnd.choice(status_messages)
        activity = discord.Streaming(type=1, url='https://www.youtube.com/watch?v=4xDzrJKXOOY', name=smsg)
        await mlky.change_presence(status=discord.Status.online, activity=activity)
        await asyncio.sleep(60) #Seconds


async def get_youtube_info(url, requester):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': False if 'playlist' in url else True,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'socket_timeout': 10,  # Increase socket timeout
        'retries': 10,         # YT-DLP's own retry mechanism
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Format duration into readable time
            duration = info.get('duration', 0)
            formatted_duration = str(timedelta(seconds=duration))
            if formatted_duration.startswith('0:'):
                formatted_duration = formatted_duration[2:]

            # Create info dict
            video_info = {
                'title': info.get('title', 'Unknown'),
                'url': url,
                'stream_url': info.get('url', None),
                'thumbnail': info.get('thumbnail', None),
                'channel': info.get('uploader', 'Unknown'),
                'channel_url': info.get('uploader_url', None),
                'duration': formatted_duration,
                'duration_seconds': duration,
                'views': info.get('view_count', 0),
                'likes': info.get('like_count', 0),
                'upload_date': info.get('upload_date', 'Unknown'),
                'requester': requester,
                'requester_name': requester.display_name,
                'requester_avatar': requester.avatar.url if requester.avatar else None
            }
            return video_info

    except Exception as e:
        print(f"Error fetching YouTube info: {e}")
        return None




async def extract_playlist_urls(url):
    """Extract all video URLs from a YouTube playlist."""
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'dump_single_json': True,
        'source_address': '0.0.0.0',
        'socket_timeout': 10,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' not in info:
                return []

            # Just get the URLs
            video_urls = []
            for entry in info['entries']:
                if entry and 'id' in entry:
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    video_urls.append(video_url)

            return video_urls
    except Exception as e:
        print(f"Error extracting playlist URLs: {e}")
        return []




async def play_next(ctx, guild_queue):
    """Play the next track in the queue."""
    if not guild_queue.queue:
        if guild_queue.is_playing:
            guild_queue.is_playing = False
            guild_queue.current_track = None
            guild_queue.position = 0

            # Use a new message instead of editing expired one
            await ctx.followup.send("Queue is empty. Playback finished.")
        return

    # Get the next item (URL and requester)
    next_item = guild_queue.get_next()
    if not next_item:
        guild_queue.is_playing = False
        guild_queue.current_track = None
        return
    guild_queue.position += 1

    # Fetch the full info for this track
    video_info = await get_youtube_info(next_item['url'], next_item['requester'])
    if not video_info:
        await ctx.followup.send(f"❌ Failed to fetch info for the next track. Skipping...")
        return await play_next(ctx, guild_queue)

    guild_queue.current_track = video_info

    # Set up audio player
    try:
        audio_source = discord.FFmpegPCMAudio(
            video_info['stream_url'],
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10 -timeout 10000000',
            options='-vn -bufsize 64k'
        )

        transformed_source = discord.PCMVolumeTransformer(audio_source, volume=0.5)

        # Define callback function that will be called when the song ends
        def after_playing(error):
            if error:
                print(f"Player error: {error}")

            # Schedule next song in event loop
            asyncio.run_coroutine_threadsafe(play_next(ctx, guild_queue), ctx.bot.loop)

        # Play the track
        guild_queue.voice_client.play(transformed_source, after=after_playing)
        guild_queue.is_playing = True
        guild_queue.is_paused = False
        await send_now_playing_embed(ctx, video_info, guild_queue)

    except Exception as e:
        print(f"Error playing track: {e}")
        guild_queue.is_playing = False
        guild_queue.current_track = None
        await ctx.followup.send(f"Error playing track: {str(e)}")
        asyncio.run_coroutine_threadsafe(play_next(ctx, guild_queue), ctx.bot.loop)




async def send_now_playing_embed(ctx, track, guild_queue):
    if not track:
        return

    rnd_hex = random_hex_color()
    embed = discord.Embed(
        title=track['title'],
        url=track['url'],
        color=rnd_hex
    )

    # Ensure correct queue position count
    queue_position = guild_queue.position
    guild_queue_length = guild_queue.queue_length() + guild_queue.position

    embed.set_author(name=f"Added by {track['requester_name']}", icon_url=track['requester_avatar'])
    embed.set_thumbnail(url=track['thumbnail'])

    embed.add_field(name="Channel", value=f"[{track['channel']}]({track['channel_url']})", inline=True)
    embed.add_field(name="Duration", value=track['duration'], inline=True)
    embed.add_field(name="Views", value=f"{track['views']:,}", inline=True)

    if track.get('likes'):
        embed.add_field(name="Likes", value=f"{track['likes']:,}", inline=True)

    # Convert YYYYMMDD to a more readable format
    if track['upload_date'] and track['upload_date'] != 'Unknown':
        date = track['upload_date']
        formatted_date = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
        embed.add_field(name="Upload Date", value=formatted_date, inline=True)

    # Add queue status
    embed.add_field(name="Queue Position", value=f"Track {queue_position}/{guild_queue_length}", inline=True)
    embed.set_footer(text="🎵 Now Playing 🎵")

    if guild_queue.now_playing_message:
        try:
            await guild_queue.now_playing_message.delete()
        except discord.errors.NotFound:
            # Message already deleted, ignore
            pass
        except Exception as e:
            print(f"Error deleting previous now playing message: {e}")

    # Send the new message and store its reference
    new_msg = await ctx.channel.send(embed=embed)
    guild_queue.now_playing_message = new_msg
# +++++++++++ Async Functions, buttons, modals, etc. +++++++++++ #












####################################################################################
#                                                                                  #
#                                Client Setup                                      #
#                                                                                  #
####################################################################################
intents = discord.Intents.default()
mlky = discord.Bot(intents=intents)
music_queue = MusicQueue()
# +++++++++++ Client Setup +++++++++++ #










####################################################################################
#                                                                                  #
#                                   Events                                         #
#                                                                                  #
####################################################################################
startup_spinner = Spinner(ARC, "Starting up....")
startup_spinner.start()
@mlky.event
async def on_ready():
    global author_logo
    me = await mlky.fetch_user(254148960510279683)
    author_logo = me.avatar
    mlky.loop.create_task(status())

    startup_spinner.stop()
    clear()
    print(f'Logged in as {mlky.user} (ID: {mlky.user.id})')
    print('------')

# +++++++++++ Events +++++++++++ #













####################################################################################
#                                                                                  #
#                             Regular Commands                                     #
#                                                                                  #
####################################################################################
@mlky.slash_command(name='help', description='Shows you all available commands for mulky.')
async def help(ctx):
    await ctx.defer()
    bot_avatar = ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
    rnd_hex = random_hex_color()
    embed = discord.Embed(
        title="Mulky's Music Player",
        description="Your personal music companion for discord.",
        color=rnd_hex,
    )
    embed.set_thumbnail(url=bot_avatar)

    embed.add_field(name="\u200b", value="", inline=False) #spacer

    embed.add_field(
        name="🎵 Music Commands",
        value=(
            "> **/play** - `Play a YouTube video or add it to queue`\n"
            "> **/stream** - `Stream YT live audio to the VC`\n"
            "> **/skip** - `Skip to the next song in queue`\n"
            "> **/queue** - `Show the current music queue`\n"
            "> **/clear** - `Clear the entire music queue`\n"
            "> **/stop** - `Stop playback and clear the queue`\n"
            "> **/leave** - `Disconnect from voice channel`"
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(
        name="🔊 Volume Controls",
        value=(
            "> **/volume_up** - `Increase volume by 10%`\n"
            "> **/volume_down** - `Decrease volume by 10%`\n"
            "> **/volume** - `Set volume to specific percentage`"
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="\u200b", inline=False)

    embed.add_field(
        name="💡 Pro Tips",
        value=(
            "• You can add multiple songs to create a playlist\n"
            "• The bot will automatically play the next song\n"
            "• Use `/queue` to see what's coming up next"
        ),
        inline=False
    )

    embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
    author_info = f"Created by {__authors__}"
    embed.set_footer(text=author_info, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.followup.send(embed=embed)




@mlky.slash_command(name='ping', description='Test to see if the bot is responsive.')
async def ping(ctx):
    await ctx.send_response(f"⏱️ Pong! ⏱️\nConnection speed is {round(mlky.latency * 1000)}ms", ephemeral=True)





@mlky.slash_command(name="play", description="Play a YouTube video or playlist.")
async def play(ctx, url: discord.Option(str, "The YouTube URL or playlist URL to play")):
    await ctx.defer()

    if not is_youtube_url(url):
        await ctx.followup.send("❌ Please provide a valid YouTube URL.", delete_after=10)
        return

    # Check if user is in a voice channel
    if ctx.author.voice is None:
        await ctx.followup.send("❌ You need to be in a voice channel to use this command.", delete_after=10)
        return

    # Get guild queue
    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    # Connect to voice channel if not already connected
    if ctx.voice_client is None:
        guild_queue.voice_client = await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

    guild_queue.voice_client = ctx.voice_client

    # Check if the URL is a playlist
    if is_youtube_playlist(url):
        await ctx.followup.send("📋 Processing playlist...", delete_after=25)

        # Extract videos from the playlist
        video_urls = await extract_playlist_urls(url)
        if not video_urls:
            await ctx.followup.send("❌ Failed to fetch playlist or playlist is empty.", delete_after=10)
            return

        # Add URLs to queue without fetching full info yet
        for video_url in video_urls:
            guild_queue.add(video_url, ctx.author)

        await ctx.followup.send(f"✅ - {len(video_urls)} tracks from playlist added to queue!", delete_after=10)

    else:
        # Add single URL to queue
        guild_queue.add(url, ctx.author)
        position = guild_queue.position + 1

        # If playing already, show a simple message that it was added
        if guild_queue.is_playing:
            # Just show a basic message since we don't have full info yet
            await ctx.followup.send(f"✅ - Track added to queue at position #{position}", delete_after=10)

    # If nothing is playing, start playing
    if not guild_queue.is_playing:
        await ctx.followup.send(f"✅ - Track added to queue at position #{position}", delete_after=10)
        await play_next(ctx, guild_queue)



@mlky.slash_command(name="skip", description="Skip the current song.")
async def skip(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if not guild_queue.is_playing:
        await ctx.followup.send("❌ Nothing is playing right now.")
        return

    guild_queue.voice_client.stop()  # This will trigger the after_playing callback
    await ctx.followup.send("⏭️ Skipped the current song!", delete_after=10)




@mlky.slash_command(name="queue", description="Show the current queue.")
async def queue(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if guild_queue.current_track is None and len(guild_queue.queue) == 0:
        await ctx.followup.send("The queue is empty.")
        return

    embed = discord.Embed(
        title="🎶 Music Queue 🎶",
        description="Showing you what is currently playing, what is up next, and more!",
        color=discord.Color.blue()
    )

    # Current track (this still has full info)
    if guild_queue.current_track:
        current = guild_queue.current_track
        embed.add_field(
            name="🔊 Now Playing",
            value=f"[{current['title']}]({current['url']}) | `{current['duration']}` | Requested by {current['requester_name']}",
            inline=False
        )
        embed.add_field(name="\u200b", value="", inline=False)


    # Queue - fetch info just for display
    queue_list = guild_queue.get_queue_list()
    if queue_list:
        await ctx.followup.send("Fetching queue information...(Please be patient)")

        # First track in queue gets special treatment
        upcoming_text = ""
        display_limit = min(6, len(queue_list))  # Display at most 6 tracks

        # Fetch basic info for the tracks to display
        for i, item in enumerate(queue_list[:display_limit], 2):
            # Fetch video info just for display purposes
            try:
                # We could create a lighter version of get_youtube_info to just fetch titles
                # But for simplicity, we'll use the existing function
                video_info = await get_youtube_info(item['url'], item['requester'])

                if video_info:
                    if i == 2:  # Next track gets special formatting
                        embed.add_field(
                            name="⏭️ Up Next",
                            value=f"[{video_info['title']}]({video_info['url']}) | `{video_info['duration']}` | {video_info['requester_name']}",
                            inline=False
                        )
                        embed.add_field(name="\u200b", value="", inline=False)
                    else:  # Add to the list of upcoming tracks
                        upcoming_text += f"`{i}.` [{video_info['title']}]({video_info['url']}) | `{video_info['duration']}` | {video_info['requester_name']}\n"
                else:
                    # Fallback if we couldn't get info
                    requester_name = item['requester'].display_name if hasattr(item['requester'], 'display_name') else "Unknown"
                    if i == 2:
                        embed.add_field(
                            name="⏭️ Up Next",
                            value=f"[YouTube Video]({item['url']}) | Requested by {requester_name}",
                            inline=False
                        )
                        embed.add_field(name="\u200b", value="", inline=False)
                    else:
                        upcoming_text += f"`{i}.` [YouTube Video]({item['url']}) | Requested by {requester_name}\n"

            except Exception as e:
                print(f"Error fetching video info for queue display: {e}")
                requester_name = item['requester'].display_name if hasattr(item['requester'], 'display_name') else "Unknown"
                if i == 2:
                    embed.add_field(
                        name="⏭️ Up Next",
                        value=f"[YouTube Video]({item['url']}) | Requested by {requester_name}",
                        inline=False
                    )
                    embed.add_field(name="\u200b", value="", inline=False)
                else:
                    upcoming_text += f"`{i}.` [YouTube Video]({item['url']}) | Requested by {requester_name}"


        if upcoming_text:
            if len(queue_list) > display_limit:
                upcoming_text += f"\n... and {len(queue_list) - display_limit} more tracks 🎵"

            embed.add_field(name="📋 Coming Up", value=upcoming_text, inline=False)

    # Queue stats
    total_tracks = len(queue_list) + (1 if guild_queue.current_track else 0)
    embed.set_footer(text=f"📊 Total tracks in queue: {total_tracks}")

    # Edit the original message or send a new one
    await ctx.followup.send(embed=embed)





@mlky.slash_command(name="clear", description="Clear the music queue.")
async def clearQ(ctx):
    await ctx.defer()
    guild_queue = music_queue.get_guild_queue(ctx.guild.id)
    guild_queue.clear()
    guild_queue.position = 0  # Reset position to the beginning
    guild_queue.now_playing_message = None  # Reset the currently playing message reference
    await ctx.followup.send("✨ Music queue has been cleared! 🧹", delete_after=10)




@mlky.slash_command(name="stop", description="Stop playing and clear the queue.")
async def stop(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if guild_queue.voice_client:
        guild_queue.voice_client.stop()

    guild_queue.clear()
    guild_queue.is_playing = False
    guild_queue.current_track = None
    guild_queue.position = 0
    guild_queue.now_playing_message = None
    await ctx.followup.send("✨ Playback stopped and queue cleared! 🧹", delete_after=10)




@mlky.slash_command(name="pause", description="Pause the current song.")
async def pause(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if not guild_queue.is_playing:
        await ctx.followup.send("❌ Nothing is playing right now.", delete_after=10)
        return

    if guild_queue.is_paused:
        await ctx.followup.send("⏸️ Music is already paused!", delete_after=10)
        return

    guild_queue.voice_client.pause()
    guild_queue.is_paused = True

    await ctx.followup.send("⏸️ Paused the music!", delete_after=10)




@mlky.slash_command(name="resume", description="Resume the paused song.")
async def resume(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if not guild_queue.is_playing:
        await ctx.followup.send("❌ Nothing is playing right now.", delete_after=10)
        return

    if not guild_queue.is_paused:
        await ctx.followup.send("▶️ Music is already playing!", delete_after=10)
        return

    guild_queue.voice_client.resume()
    guild_queue.is_paused = False

    await ctx.followup.send("▶️ Resumed the music!", delete_after=10)



@mlky.slash_command(name="leave", description="Leave the voice channel.")
async def leave(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if not ctx.voice_client:
        await ctx.followup.send("I'm not in a voice channel.", delete_after=10)
        return

    # Stop playback and clear queue before leaving
    if guild_queue.voice_client:
        guild_queue.voice_client.stop()

    guild_queue.clear()
    guild_queue.is_playing = False
    guild_queue.current_track = None
    guild_queue.voice_client = None

    await ctx.voice_client.disconnect()
    await ctx.followup.send("Disconnected from voice channel.", delete_after=10)




@mlky.slash_command(name="volume_up", description="Increase the volume by 10%")
async def volume_up(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if not ctx.voice_client or not guild_queue.is_playing:
        await ctx.followup.send("Nothing is playing right now.", delete_after=10)
        return

    source = ctx.voice_client.source

    if not isinstance(source, discord.PCMVolumeTransformer):
        await ctx.followup.send("Can't adjust volume for the current audio source.", delete_after=10)
        return

    # Increase volume by 10% (0.1), max at 200% (2.0)
    current_volume = source.volume
    new_volume = min(2.0, current_volume + 0.1)
    source.volume = new_volume

    volume_percent = int(new_volume * 100)
    await ctx.followup.send(f"Volume increased to {volume_percent}%")




@mlky.slash_command(name="volume_down", description="Decrease the volume by 10%")
async def volume_down(ctx):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if not ctx.voice_client or not guild_queue.is_playing:
        await ctx.followup.send("Nothing is playing right now.", delete_after=10)
        return

    source = ctx.voice_client.source

    if not isinstance(source, discord.PCMVolumeTransformer):
        await ctx.followup.send("Can't adjust volume for the current audio source.", delete_after=10)
        return

    # Decrease volume by 10% (0.1), min at 0% (0.0)
    current_volume = source.volume
    new_volume = max(0.0, current_volume - 0.1)
    source.volume = new_volume

    volume_percent = int(new_volume * 100)
    await ctx.followup.send(f"Volume decreased to {volume_percent}%", delete_after=10)




@mlky.slash_command(name="volume", description="Set the volume to a specific custom level.")
async def volume(ctx, percentage: discord.Option(int, "Volume percentage (0-200)", min_value=0, max_value=200)):
    await ctx.defer()

    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    if not ctx.voice_client or not guild_queue.is_playing:
        await ctx.followup.send("Nothing is playing right now.", delete_after=10)
        return

    source = ctx.voice_client.source

    if not isinstance(source, discord.PCMVolumeTransformer):
        await ctx.followup.send("Can't adjust volume for the current audio source.", delete_after=10)
        return

    new_volume = percentage / 100
    source.volume = new_volume
    await ctx.followup.send(f"Volume set to {percentage}%", delete_after=10)








@mlky.slash_command(name="stream", description="Stream live YouTube audio to the voice channel", guild_ids=[1247190936111288361, 1079973042861654116])
async def stream(ctx, url: discord.Option(str, "The YouTube live stream URL")):
    await ctx.defer()

    # Validate it's a YouTube URL
    if not check_live_url(url):
        await ctx.followup.send("❌ Please provide a valid YouTube URL.", delete_after=10)
        return

    # Check if user is in a voice channel
    if ctx.author.voice is None:
        await ctx.followup.send("❌ You need to be in a voice channel to use this command.", delete_after=10)
        return

    # Get guild queue
    guild_queue = music_queue.get_guild_queue(ctx.guild.id)

    # Connect to voice channel if not already connected
    if ctx.voice_client is None:
        guild_queue.voice_client = await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

    guild_queue.voice_client = ctx.voice_client

    # Fetch stream information
    await ctx.followup.send("🔴 Connecting to livestream...", delete_after=5)

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0',
        'socket_timeout': 10,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            is_live = info.get('is_live', False)
            if not is_live:
                await ctx.followup.send("⚠️ This doesn't appear to be a live stream URL. Use `/play` for regular videos instead.", delete_after=10)
                return

            stream_url = info.get('url', None)
            title = info.get('title', 'Unknown Stream')
            thumbnail = info.get('thumbnail', None)
            channel = info.get('uploader', 'Unknown')
            channel_url = info.get('uploader_url', None)
            viewers = info.get('concurrent_viewers', 0)

            if guild_queue.voice_client.is_playing():
                guild_queue.voice_client.stop()

            guild_queue.clear()
            guild_queue.is_playing = False
            guild_queue.current_track = None

            audio_source = discord.FFmpegPCMAudio(
                stream_url,
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -reconnect_on_network_error 1 -reconnect_on_http_error 4xx,5xx -http_persistent 0',
                options='-vn -bufsize 512k'
            )

            transformed_source = discord.PCMVolumeTransformer(audio_source, volume=0.5)

            # Play the stream audio.
            def after_streaming(error):
                if error:
                    print(f"Stream error: {error}")
                guild_queue.is_playing = False

            guild_queue.voice_client.play(transformed_source, after=after_streaming)
            guild_queue.is_playing = True

            rnd_hex = random_hex_color()
            embed = discord.Embed(
                title=f"🔴 {title}",
                url=url,
                color=rnd_hex,
                description="**Now streaming live audio**"
            )

            embed.set_author(
                name=f"Stream started by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )

            if thumbnail:
                embed.set_thumbnail(url=thumbnail)

            embed.add_field(
                name="📺 Channel",
                value=f"[{channel}]({channel_url})" if channel_url else channel,
                inline=True
            )

            if viewers > 0:
                embed.add_field(
                    name="👥 Viewers",
                    value=f"{viewers:,}",
                    inline=True
                )

            embed.add_field(
                name="🎵 Status",
                value="🟢 Live",
                inline=True
            )

            embed.add_field(
                name="🎮 Controls",
                value=(
                    "`/volume_up` • `/volume_down` • `/volume`\n"
                    "`/pause` • `/resume` • `/leave`"
                ),
                inline=False
            )

            embed.add_field(
                name="ℹ️ Notice",
                value="Livestreams play continuously until you stop them or leave the channel.",
                inline=False
            )

            embed.set_footer(
                text="🔴 Live Stream",
                icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
            )
            embed.timestamp = datetime.datetime.now()
            await ctx.followup.send(embed=embed)

    except Exception as e:
        print(f"Error streaming: {e}")
        await ctx.followup.send(f"❌ Failed to start stream: {str(e)}", delete_after=15)
        guild_queue.is_playing = False
# +++++++++++ Regular Commands +++++++++++ #


















if __name__ == '__main__':
    clear()
    mlky.run(token, reconnect=True)
