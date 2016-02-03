#!/usr/bin/env python3.5
import discord
import asyncio
import logging
import youtube_dl
from random import choice, randint, shuffle
from botconfig import settings
import re
import datetime
from os import path, listdir
import os
import pprint
import urllib
import traceback
import json

with open("json/blacklist.json", encoding='utf-8', mode="r") as f:
    blacklisted_users = json.loads(f.read())

youtube_dl_options = {
	'format': 'bestaudio/best',
	'extractaudio': True,
	'audioformat': "mp3",
	'outtmpl': '%(id)s',
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': True,
	'quiet': True,
	'no_warnings': True,
	'outtmpl': "music/%(id)s"}
greetings = ["Hey.", "Yes?", "Hi.", "I'm listening.", "Hello.", "I'm here.", "Mmhmm?"]
greetings_caps = ["DON'T SCREAM", "WHAT", "WHAT IS IT?!", "ì_ì", "NO CAPS LOCK"]

client = discord.Client()

if not discord.opus.is_loaded():
	discord.opus.load_opus('libopus-0.dll')

def loadHelp():
    global bot_help, audio_help
    bot_help = """**Command list**:
    !flip - I'll flip a coin.
    !roll *number* - I'll roll a dice with the max number that you set.
    !choice - I'll choose the option (seperate options with commas \",\")
    !servers - Gets the servers I am connected to.
    !ts - Heres the IP for Envexia's TS...if its ever needed again.
    !evajoin *link* - I'll join your server!
    !goog *search* - Let me google that for you...

    !help - I'll send you this help message
    !audio help - I'll send you help for the music I can play
    """
    audio_help = """**Audio help**:
    !play *youtubeLink* - I'll download the youtube audio and play it for you :)
    !pause - I'll hit the pause button if there is music on.
    !resume - I'll hit the resume button if there is music paused.
    !stop - bye :(
    !volume *0.00-1.00* - Turn the music up! (or down)
    """

@client.async_event
async def on_message(message):
    if message.author == client.user:
        return

    # if message.author.id in blacklisted_users and not isMemberAdmin(message):
    #     return False
    global greetings
    global greetings_caps
    global option
    global dsave
    global imagesList
    member = discord.utils.find(lambda m: m.name == message.author.name , message.channel.server.members)

    if message.content == client.user.name.upper() or message.content == client.user.name.upper() + "?":
        await client.send_message(message.channel, "`" + choice(greetings_caps) + "`")
    elif message.content.lower() == client.user.name.lower() + "?":
        await client.send_message(message.channel, "`" + choice(greetings) + "`")
    elif message.content == client.user.mention + " ?" or message.content == client.user.mention + "?":
        await client.send_message(message.channel, "`" + choice(greetings) + "`")
    ######################## Help ########################
    elif message.content.startswith('!help'):
        await client.send_message(message.author, bot_help)
        await client.send_message(message.channel, "{} `Check your DMs for the command list.`".format(message.author.mention))
    elif message.content.startswith('!audio help'):
        await client.send_message(message.author, audio_help)
        await client.send_message(message.channel, "{} `Check your DMs for the command list.`".format(message.author.mention))

    elif message.content.startswith('!admin'):
        result = isMemberAdmin(message)
        print(result)
    elif message.content.startswith('!findid'):
        name = discord.utils.find(lambda m: m.name == 'Dozy', message.channel.server.members)
        print(name.id)
        name = discord.utils.find(lambda m: m.name == 'Casaiya', message.channel.server.members)
        print(name.id)
    ######################## Random functions ########################
    elif message.content.startswith('!choice'):
        await randomChoice(message)
    elif message.content.startswith('!coin'):
        await coinFlip(message)
    elif message.content.startswith('!roll'):
        await roll(message)
    ######################## Utility ########################
    elif message.content.startswith('!servers'):
        await getServers(message)
    elif message.content.startswith('!ts'):
        await teamspeak(message)
    elif message.content.startswith('!evajoin '):
        await joinServer(message)
    ######################## Fun stuff ########################
    elif message.content.startswith('!goog'):
        await google(message)
    elif message.content.lower().startswith('!liu'):
        await liu(message)
    elif message.content.lower().startswith('!ruth'):
        await ruth(message)
    elif message.content.lower().startswith('!dozy'):
        await dozy(message)
    elif message.content.lower().startswith('!shen'):
        await shen(message)
    elif message.content.lower().startswith('!whats up'):
        await whatsUp(message)
    ######################## Music ########################
    elif message.content.lower().startswith('!youtube') or message.content.lower().startswith('!play'):
        await playVideo(message)
    elif message.content.lower().startswith('!pause'):
        if currentPlaylist: currentPlaylist.pause()
    elif message.content.lower().startswith('!resume'):
        if currentPlaylist: currentPlaylist.resume()
    elif message.content.lower().startswith('!stop'):
        await leaveVoice()
    elif message.content.lower().startswith('!volume'):
        await setVolume(message)
        #Images
    else:
        for image in imagesList:
            imagelower = image.lower()[:-4]
            if message.content.lower().find(imagelower+' ') != -1 or message.content.lower().endswith(imagelower):
                await client.send_file(message.channel, './twitchimages/'+image)

    #Music
async def playVideo(message):
    global musicPlayer, currentPlaylist
    toDelete = None
    if await checkVoice(message):
        pattern = "(?:youtube\.com\/watch\?v=)(.*)|(?:youtu.be/)(.*)"
        rr = re.search(pattern, message.content, re.I | re.U)
        if rr.group(1) != None:
            id = rr.group(1)
        elif rr.group(2) != None:
            id = rr.group(2)
        else:
            await client.send_message(message.channel, "{} `Invalid link.`".format(message.author.mention))
            return False
        stopMusic()
        if settings["DOWNLOADMODE"]:
            toDelete = await client.send_message(message.channel, "`I'm in download mode. It might take a bit for me to start. I'll delete this message as soon as I'm ready.`".format(id, message.author.name))
        data = {"filename" : 'https://www.youtube.com/watch?v=' + id, "type" : "singleSong"}
        currentPlaylist = Playlist(data)
        if canDeleteMessages(message):
            await client.send_message(message.channel, "`Playing youtube video {} requested by {}`".format(await getTitle(data["filename"]), message.author.name))
            await client.delete_message(message)
        if toDelete:
            await client.delete_message(toDelete)

async def getTitle(url):
    try:
        yt = youtube_dl.YoutubeDL(youtube_dl_options)
        v = yt.extract_info(url, download=False)
        return v['title']
    except:
        return False

def stopMusic():
    global musicPlayer, currentPlaylist
    if currentPlaylist != None:
	    currentPlaylist.stop = True
    if musicPlayer != None:
	    musicPlayer.stop()

async def checkVoice(message):
    if not client.is_voice_connected():
        if message.author.voice_channel:
            if message.author.voice_channel.permissions_for(message.server.me).connect:
                await client.join_voice_channel(message.author.voice_channel)
            else:
                await client.send_message(message.channel, "{} `I need permissions to join that channel.`".format(message.author.mention))
                return False
        else:
            await client.send_message(message.channel, "{} `You need to join a voice channel first.`".format(message.author.mention))
            return False
    elif client.is_voice_connected() != message.author.voice_channel:
        if message.author.voice_channel:
            if message.author.voice_channel.permissions_for(message.server.me).connect:
                await client.voice.disconnect()
                await client.join_voice_channel(message.author.voice_channel)
            else:
                await client.send_message(message.channel, "{} `I need permissions to join that channel.`".format(message.author.mention))
                return False
        else:
            await client.send_message(message.channel, "{} `You need to join a voice channel first.`".format(message.author.mention))
            return False
    return True

async def leaveVoice():
    if client.is_voice_connected():
        stopMusic()
        await client.voice.disconnect()

async def setVolume(message):
    global settings
    msg = message.content
    if len(msg.split(" ")) == 2:
        msg = msg.split(" ")
        try:
            vol = float(msg[1])
            if vol >= 0 and vol <= 1:
                settings["VOLUME"] = vol
                await(client.send_message(message.channel, "`Volume set. Next track will have the desired volume.`"))
            else:
                await(client.send_message(message.channel, "`Volume must be between 0 and 1. Example: !volume 0.50`"))
        except:
            await(client.send_message(message.channel, "`Volume must be between 0 and 1. Example: !volume 0.15`"))
    else:
        await(client.send_message(message.channel, "`Volume must be between 0 and 1. Example: !volume 0.15`"))

class Playlist():
    def __init__(self, filename=None):
        self.filename = filename
        self.current = 0
        self.stop = False
        self.lastAction = 999
        self.currentTitle = ""
        self.type = filename["type"]
        if filename["type"] == "singleSong":
            self.playlist = [filename["filename"]]
            self.playSong(self.playlist[0])
        else:
            raise("Invalid playlist call.")

    def playSong(self, url):
        global musicPlayer
        if settings["DOWNLOADMODE"]:
            v = self.getVideo(url)
            logger.info(v)
            if musicPlayer:
                if musicPlayer.is_playing():
                    musicPlayer.stop()
            if v:
                logger.info("starting track from ffmpeg...")
                musicPlayer = client.voice.create_ffmpeg_player("music/" + v, options='''-filter:a "volume={}"'''.format(settings["VOLUME"]))
                musicPlayer.start()
        else:
            if musicPlayer:
                if musicPlayer.is_playing():
                    musicPlayer.stop()
            logger.info("starting track from ytdl...")
            musicPlayer = client.voice.create_ytdl_player(self.playlist[0], options=youtube_dl_options)
            musicPlayer.start()

    def getVideo(self, url):
        try:
            yt = youtube_dl.YoutubeDL(youtube_dl_options)
            v = yt.extract_info(url, download=False)
            if not os.path.isfile("music/" + v["id"]):
                logger.info("Track not in music folder, downloading...")
                v = yt.extract_info(url, download=True)
            self.currentTitle = v["title"]
            return v["id"]
        except Exception as e:
            logger.error(e)
            return False

    def passedTime(self):
        return abs(self.lastAction - int(time.perf_counter()))

    def pause(self):
        if musicPlayer.is_playing() and not self.stop:
            musicPlayer.pause()

    def resume(self):
        if not self.stop:
            musicPlayer.resume()


async def randomChoice(message):
    choices = message.content[8:].split(',')
    random = randint(0, len(choices)-1)
    await client.send_message(message.channel, choices[random])

async def coinFlip(message):
    roll = randint(0, 1)
    if (roll == 0):
        coin = "heads"
    elif (roll == 1):
        coin = "tails"
    await client.send_message(message.channel, '{} flipped a coin and it landed on '.format(message.author.mention) + coin)

async def roll(message):
    rollMax = message.content[6:]
    if rollMax == '':
        rollMax = '100'
    roll = randint(0, int(rollMax))
    await client.send_message(message.channel, '{} rolled a '.format(message.author.mention) + str(roll))

async def getServers(message):
    servers = []
    for server in client.servers:
        servers.insert(0 , server.name)
    await client.send_message(message.channel, ', '.join(servers))

async def teamspeak(message):
    await client.send_message(message.channel, 'Teamspeak IP: 88.202.226.151:7297')

async def joinServer(message):
    inviteLink = message.content[10:]
    client.accept_invite(inviteLink)

async def google(message):
    query = urllib.parse.quote_plus(message.content[8:])
    await client.send_message(message.channel, 'http://lmgtfy.com/?q='+query)

async def liu(message):
    liu = discord.utils.find(lambda m: m.id == '105714564930260992', message.channel.server.members)
    if (liu == None):
        await client.send_message(message.channel, 'Liu is not on this server, but if he was I would call him the best person in the universe.')
    else:
        await client.send_message(message.channel, '{}, Biggest blizzard fanboi worldwide.'.format(liu.mention))
        await client.send_file(message.channel, 'images/liu.jpg')

async def ruth(message):
    ruth = discord.utils.find(lambda m: m.id == '105694204285460480', message.channel.server.members)
    if (ruth == None):
        await client.send_message(message.channel, 'Ruth is not on this server.')
    else:
        await client.send_message(message.channel, '{}, SHARK!'.format(ruth.mention))
        await client.send_file(message.channel, 'images/hugme.jpg')

async def dozy(message):
    dozy = discord.utils.find(lambda m: m.id == '105308157592481792', message.channel.server.members)
    if (dozy == None):
        await client.send_message(message.channel, 'Dozy is not on this server.')
    else:
        await client.send_message(message.channel, '{}, in his natural habitat.'.format(dozy.mention))
        await client.send_file(message.channel, 'images/dozydog.jpg')

async def shen(message):
    shenji = discord.utils.find(lambda m: m.id == '105328844113719296', message.channel.server.members)
    if (shenji == None):
        await client.send_message(message.channel, 'Shenji is not on this server.')
    else:
        await client.send_message(message.channel, '{}, is better than liu.'.format(shenji.mention))

async def whatsUp(message):
    await client.send_message(message.channel, 'The sky.')

@client.async_event
def on_ready():
    logger.info("I'm online " + "(" + client.user.id + ")")

def isMemberAdmin(message):
	if not message.channel.is_private:
		if discord.utils.get(message.author.roles, name="Admin") != None:
			return True
		else:
			return False
	else:
		return False

def canDeleteMessages(message):
    return message.channel.permissions_for(message.server.me).manage_messages

def loggerSetup():
    #api wrapper
    logger = logging.getLogger('discord')
    logger.setLevel(logging.WARNING)
    handler = logging.FileHandler(filename='wrapper.log', encoding='utf-8', mode='a')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt="[%d/%m/%Y %H:%M]"))
    logger.addHandler(handler)
    #Red
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt="[%d/%m/%Y %H:%M]"))
    logger.addHandler(handler)
    return logger

def loadDataFromFiles():
    global imagesList
    loadHelp()
    imagesList = []
    for f in listdir('twitchimages/'):
        imagesList.append(f)
    logger.info("loaded files.")

def main():
    global settings, logger, client, musicPlayer, currentPlaylist, imagesList

    logger = loggerSetup()

    loadDataFromFiles()

    musicPlayer = None
    currentPlaylist = None

    yield from client.login(settings["EMAIL"], settings["PASSWORD"])
    yield from client.connect()

if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(main())
	except discord.LoginFailure:
		logger.error("The credentials you put in settings.json are wrong. Take a look.")
	except Exception as e:
		logger.error(e)
		loop.run_until_complete(client.logout())
	finally:
		loop.close()



### Old code    |
#               |
#               v

# def download_song(ytUrl):
#     savedir = "music"
#     if 'youtube' in ytUrl:
#         if '&' in ytUrl:
#             endStart = ytUrl.find('&')
#             songURL = ytUrl[ :endStart]
#             songURL.strip()
#         else:
#             songURL = ytUrl
#     else:
#         songURL = ytUrl
#     ydlOptions = {
#     'format' : 'bestaudio/best',
#     'extractaudio' : True,
#     'audioformat' : 'mp3',
#     'outtmpl' : '%(id)s',
#     'noplaylist' : True,
#     }
#     print(songURL)
#     ydl = youtube_dl.YoutubeDL(ydlOptions)
#     try:
#         info = ydl.extract_info(songURL, download=False)
#         title = info['title']
#         savepath = os.path.join(savedir, "%s.mp3" % (title))
#     except Exception as e:
#         print("Can't access song %s\n" % traceback.format_exc())
#         return 'FACK!'
#     try:
#         os.stat(savepath)
#         return savepath
#     except OSError:
#         try:
#             result = ydl.extract_info(songURL, download=True)
#             os.rename(result['id'], savepath)
#             return savepath
#         except Exception as e:
#             print("Can't download audio! %s\n" % traceback.format_exc())
#             return 'FACK!'
