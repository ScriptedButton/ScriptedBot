import discord
import random
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from util.EasyData import EasyData
from discord.ext import commands

class Song:
    def __init__(self, requestee=None, duration=None, voice_channel=None, url=None, name=None, server=None):
        self.requested_by = requestee
        self.voice_channel = voice_channel
        self.url = url
        self.name = name
        self.server = server
        self.duration = duration

a = EasyData("botdata.txt")
temp_data = a.getAsDict()
player = None

music_queue = dict()
players = dict()

bot = commands.Bot(command_prefix="!", description="Experimental bot.")

logging = True
choices = dict()

async def checkDM(userid):
    dm_enabled = temp_data[userid][1]
    if dm_enabled:
        return True
    else:
        return False

async def addQueue(server, songObj):
    if not music_queue.get(server.id):
        music_queue[server.id] = list()
        music_queue[server.id].append(songObj)
    else:
        music_queue[server.id].append(songObj)

async def strip(word):
    newurl = str()
    for i in word:
        if i == " ":
            newurl += "+"
        else:
            newurl += i
    return newurl

async def handleQuery(query):
    async with aiohttp.get("https://www.youtube.com/results?search_query=" + query) as r:
        soup = BeautifulSoup(await r.text(), 'html.parser')
        choices = list()
        for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
            choices.append(('https://www.youtube.com' + vid['href'], vid['title']))
        return choices

async def handleUpdate():
    global temp_data
    a.updateFile(temp_data)
    temp_data = a.getAsDict()


async def botEmbed(title=str(), description=str(), color=discord.Color):
    em = discord.Embed(title=title, description=description, color=color)
    em.set_footer(text="Scripted Bot")
    return em


async def musicManager():
    global player
    while True:
        await asyncio.sleep(1)
        for server in music_queue.copy():
            songs = music_queue[server]
            for song in songs.copy():
                if players.get(server) and players.get(server).is_playing():
                    pass
                else:
                    for x in list(bot.voice_clients):
                        if x.server.id == server:
                            await x.disconnect()
                    voice_channel = song.voice_channel
                    vc = await bot.join_voice_channel(voice_channel)
                    players[server] = await vc.create_ytdl_player(song.url)
                    players[server].start()
                    current_index = music_queue[server].index(song)
                    music_queue[server].pop(current_index)
            if not players[server].is_playing():
                for x in list(bot.voice_clients):
                    if x.server.id == server:
                        await x.disconnect()

@bot.event
async def on_ready():
    print("Bot loaded!")

@bot.event
async def on_command_error(err, *args, **kwargs):
    ctx = args[0]
    em = discord.Embed(title="Command Error", description=str(err), color=discord.Color.red())
    await bot.send_message(ctx.message.channel, embed=em)

@bot.event
async def on_member_join(member):
    member_id = member.id
    if not temp_data.get(member_id):
        temp_data[member_id] = [0, True]
        await handleUpdate()


@bot.command(pass_context=True)
async def bal(ctx):
    """Get the amount of money you have."""
    author_id = ctx.message.author.id
    await bot.say("Balance: " + str(temp_data[author_id][0]))

@bot.command(pass_context=True)
async def lottery(ctx):
    """Earn a random amount of money."""
    author_id = ctx.message.author.id
    money = random.randrange(1, 1000)
    temp_data[author_id][0] += money
    await handleUpdate()
    em = await botEmbed(title="Economy", description="You've earned {0}!\nYour new balance is: {1}".format(money, temp_data[author_id][0]), color=discord.Color.blue())
    await bot.say(embed=em)

@bot.command(pass_context=True)
async def yt(ctx, *url):
    """Queries YouTube for a specific search term, supplies a list of 20 songs with that term."""
    global choices
    server = ctx.message.server.id
    choice_strings = dict()
    choice_indexes = dict()
    choice_strings[server] = str()
    choices[server] = await handleQuery(await strip(url))
    choice_indexes[server] = 1
    print(choices[server])
    for url in choices[server]:
        choice_strings[server] += str(choice_indexes[server]) + ":" + url[1] + "\n"
        choice_indexes[server] += 1
    em = await botEmbed(title="Song Selection", description=choice_strings[server], color=discord.Color.blue())
    await bot.say(embed=em)

@bot.command(pass_context=True)
async def leave(ctx):
    """Makes the bot manually leave the voice channel it is connected to."""
    for x in bot.voice_clients:
        if x.server == ctx.message.server:
            return await x.disconnect()


@bot.command(pass_context=True)
async def play(ctx, choice: int):
    """Makes the bot play the selected song from YouTube query results."""
    if not ctx.message.author.voice_channel:
        em = await botEmbed(title="Error", description="You must be in a voice channel to use this command!", color=discord.Color.red())
        await bot.say(embed=em)
        return
    server = ctx.message.server.id
    global player
    global music_queue
    song = Song(name=choices[server][choice-1][1], url=choices[server][choice-1][0], voice_channel=ctx.message.author.voice_channel, server=ctx.message.server, requestee=ctx.message.author)
    await addQueue(ctx.message.server, song)
    em = await botEmbed(title="Song Added", description="The song {} has been added to the queue.".format(choices[server][choice-1][1]), color=discord.Color.blue())
    await bot.say(embed=em)

@bot.command(pass_context=True)
async def volume(ctx, volume: float):
    """Sets the volume of the bot, (0-2)."""
    server = ctx.message.server.id
    players[server].volume = volume

@bot.command(pass_context=True)
async def playing(ctx):
    """Gets information about the song that is currently playing."""
    server = ctx.message.server.id
    em = await botEmbed(title="Song Information", description="Title: " + players[server].title + "\n" + players[server].url + "\n" + "Duration: " + str(players[server].duration) + " seconds." + "\n" + "Views: " + str(players[server].views), color=discord.Color.blue())
    await bot.say(embed=em)

@bot.command(pass_context=True)
async def q(ctx):
    """Supplies a list of the songs in the queue."""
    server = ctx.message.server.id
    q_string = str()
    q_index = 1
    for url in music_queue[server]:
        q_string += str(q_index) + ":" + url.name + "\n"
        q_index += 1
    em = await botEmbed(title="Song Selection", description=q_string, color=discord.Color.blue())
    await bot.say(embed=em)

@bot.command(pass_context=True)
async def skip(ctx):
    """Skips the currently playing song."""
    server = ctx.message.server.id
    players[server].stop()
    for x in list(bot.voice_clients):
        if x.server.id == server:
            await x.disconnect()

@bot.command(pass_context=True)
async def sharesong(ctx, user: discord.User):
    """Allows you to share a song with a user."""
    if not await checkDM(user.id):
        em = await botEmbed(title="Error", description="The specified user has disabled DMs from the bot.", color=discord.Color.red())
        await bot.say(embed=em)
        return
    server = ctx.message.server.id
    title = players[server].title
    url = players[server].url
    duration = players[server].duration
    views = players[server].views
    em = await botEmbed(title="{} has shared a song with you!".format(ctx.message.author.name), description="Title: " + players[server].title + "\n" + players[server].url + "\n" + "Duration: " + str(players[server].duration) + " seconds." + "\n" + "Views: " + str(players[server].views), color=discord.Color.blue())
    await bot.send_message(user, embed=em)
    await bot.say(embed=await botEmbed(title="Notification", description="You have shared the current song with {}".format(user.name), color=discord.Color.blue()))

@bot.command(pass_context=True)
async def disabledm(ctx):
    """Prevents the bot from DMing you."""
    temp_data[ctx.message.author.id][1] = False
    await handleUpdate()
    em = await botEmbed(title="Notification", description="You have successfully disallowed DMs from the bot.", color=discord.Color.blue())
    await bot.say(embed=em)

@bot.command(pass_context=True)
async def enabledm(ctx):
    """Allows the bot to DM you."""
    temp_data[ctx.message.author.id][1] = True
    await handleUpdate()
    em = await botEmbed(title="Notification", description="You have successfully allowed DMs from the bot.", color=discord.Color.blue())
    await bot.say(embed=em)


bot.loop.create_task(musicManager())
bot.run("...")
