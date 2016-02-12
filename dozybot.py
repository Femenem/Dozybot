#!/usr/bin/env python3.5
import discord
import asyncio
import aiohttp
import logging
import youtube_dl
import urllib
from bs4 import BeautifulSoup
from random import choice, randint, shuffle
import re
import time
from os import path, listdir
import os
import traceback
import json

from botconfig import settings
import dataIO

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
thanks = ["You're welcome.", "You are welcome.", "No problem.", "Anytime"]
thanks_caps = ["STOP YELLING", "YEAH, WHATEVER"]

client = discord.Client()

if not discord.opus.is_loaded():
	discord.opus.load_opus('libopus-0.dll')

def loadHelp():
    global bot_help, audio_help
    bot_help = """**Command list**:
    !flip - I'll flip a coin.
    !roll [number] - I'll roll a dice with the max number that you set.
    !choice - I'll choose the option (seperate options with commas \",\")
    !servers - Gets the servers I am connected to.
    !ts - Heres the IP for Envexia's TS...if its ever needed again.
    !evajoin [link] - I'll join your server!
    !goog [search] - Let me google that for you...

    !help - I'll send you this help message
    !audio help - I'll send you help for the music I can play
    """
    audio_help = """**Audio help**:
    !addplaylist [name] [link] - Adds a playlist to my list.
    !delplaylist [name] - Deletes a playlist from my list. (Dont you dare touch someone elses :P)
    !play [name] - Plays a playlist thats in my list.
    !skip - Skips the current song in the playlist
    !prev - Plays the previous song in the playlist.
    !shuffle - Shuffles the songs around in the playlist.
    !convertplaylist - Heres a link to a website that can convert your playlist into a youtube playlist!
    !pause - I'll hit the pause button if there is music on.
    !resume - I'll hit the resume button if there is music paused.
    !stop - bye :(
    !volume [0.00-1.00] - Turn the music up! (or down)
    !yt [youtubeLink] - I'll download the youtube audio and play it for you :)
    """

@client.async_event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id in blacklisted_users and not isMemberAdmin(message):
        return True

    global greetings
    global greetings_caps
    global thanks
    global option
    global dsave
    global imagesList
    member = discord.utils.find(lambda m: m.name == message.author.name , message.channel.server.members)

    ######################## hello? ########################
    if message.content == client.user.name.upper() or message.content == client.user.name.upper() + "?":
        await client.send_message(message.channel, "`" + choice(greetings_caps) + "`")
    elif message.content.lower() == client.user.name.lower() + "?":
        await client.send_message(message.channel, "`" + choice(greetings) + "`")
    elif message.content == client.user.mention + " ?" or message.content == client.user.mention + "?":
        await client.send_message(message.channel, "`" + choice(greetings) + "`")
    ######################## Thanks ########################
    elif "THANKS, " + client.user.name.upper() in message.content or "THANKS " + client.user.name.upper() in message.content:
        await client.send_message(message.channel, "`" + choice(thanks_caps) + "`")
    elif "thanks, " + client.user.name.lower() in message.content.lower() or "thanks " + client.user.name.lower() in message.content.lower():
        await client.send_message(message.channel, "`" + choice(thanks) + "`")
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
    elif '!proverb' in message.content.lower():
        await client.send_message(message.channel, "`" + choice(proverbs) + "`")
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
    elif message.content.lower().startswith('!yt'):
        await playVideo(message)
    elif message.content.lower().startswith('!play'):
        await playPlaylist(message)
    elif message.content.startswith("!addplaylist"):
        await addPlaylist(message)
    elif message.content.startswith("!delplaylist"):
        await delPlaylist(message)
    elif message.content.lower().startswith('!pause'):
        if currentPlaylist: currentPlaylist.pause()
    elif message.content.lower().startswith('!resume'):
        if currentPlaylist: currentPlaylist.resume()
    elif message.content.lower().startswith('!stop'):
        await leaveVoice()
    elif message.content.lower() == "!skip" or message.content.lower() == "!next":
        if currentPlaylist: currentPlaylist.nextSong(currentPlaylist.getNextSong())
    elif message.content.lower() == "!prev" or message.content.lower() == "!previous":
        if currentPlaylist: currentPlaylist.nextSong(currentPlaylist.getPreviousSong())
    elif message.content.lower() == "!shuffle":
        if currentPlaylist: currentPlaylist.shuffle()
    elif message.content.lower().startswith('!volume'):
        await setVolume(message)
    elif message.content.lower().startswith('!convertplaylist'):
        await client.send_message(message.channel, "`Use http://soundiiz.com to convert a spotify playlist to a youtube one.`")
    ######################## Admin Commands ########################
    elif message.content.lower().startswith('!blacklist '):
        await blacklist(message, "add")
    elif message.content.lower().startswith('!forgive'):
        await blacklist(message, "remove")
    elif message.content.lower().startswith('!blacklist'):
        await blacklist(message, "fack")
    ######################## Images ########################
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

async def addPlaylist(message):
    msg = message.content.split(" ")
    if len(msg) == 3:
        _, name, link = msg
        if isPlaylistNameValid(name) and len(name) < 25 and isPlaylistLinkValid(link):
            if dataIO.fileIO("playlists/" + name + ".json", "check"):
                await client.send_message(message.channel, "`A playlist with that name already exists.`")
                return False
            links = await parsePlaylist(link)
            if links:
                data = { "author" : message.author.id, "playlist": links}
                dataIO.fileIO("playlists/" + name + ".json", "save", data)
                await client.send_message(message.channel, "`Playlist added. Name: {}`".format(name))
            else:
                await client.send_message(message.channel, "`Something went wrong. Either the link was incorrect or I was unable to retrieve the page.`")
        else:
            await client.send_message(message.channel, "`Something is wrong with the playlist's link or its filename. Remember, the name must be with only numbers, letters and underscores. Link must be this format: https://www.youtube.com/playlist?list=PLaqmzXcdRXOSVrktmZ-SHzMW66kFixggq`")

    else:
        await client.send_message(message.channel, "`!addplaylist [name] [link]`")

async def delPlaylist(message):
    msg = message.content.split(" ")
    if len(msg) == 2:
        _, filename = msg
        if dataIO.fileIO("playlists/" + filename + ".txt", "check"):
            authorid = dataIO.fileIO("playlists/" + filename + ".txt", "load")["author"]
            if message.author.id == authorid or isMemberAdmin(message):
                os.remove("playlists/" + filename + ".txt")
                await client.send_message(message.channel, "`Playlist {} removed.`".format(filename))
            else:
                await client.send_message(message.channel, "`Only the playlist's author and admins can do that.`")
        else:
            await client.send_message(message.channel, "`There is no playlist with that name.`")
    else:
        await client.send_message(message.channel, "`!delplaylist [name]`")

def isPlaylistNameValid(name):
	for l in name:
		if l.isdigit() or l.isalpha() or l == "_":
			pass
		else:
			return False
	return True

def isPlaylistLinkValid(link):
    pattern = "^https:\/\/www.youtube.com\/playlist\?list=(.[^:/]*)"
    rr = re.search(pattern, link, re.I | re.U)
    if not rr == None:
        return rr.group(1)
    else:
        return False

async def playPlaylist(message, sing=False):
    global musicPlayer, currentPlaylist
    msg = message.content
    toDelete = None
    if msg != "!play":
        if await checkVoice(message):
            msg = message.content[6:]
            if dataIO.fileIO("playlists/" + msg + ".json", "check"):
                stopMusic()
                data = {"filename" : msg, "type" : "playlist"}
                if settings["DOWNLOADMODE"]:
                    toDelete = await client.send_message(message.channel, "`I'm in download mode. It might take a bit for me to start and switch between tracks. I'll delete this message as soon as the current playlist stops.`".format(id, message.author.name))
                currentPlaylist = Playlist(data)
                await asyncio.sleep(2)
                await currentPlaylist.songSwitcher()
                if toDelete:
                    await client.delete_message(toDelete)
            else:
                await client.send_message(message.channel, "{} `That playlist doesn't exist.`".format(message.author.mention))


async def getTitle(url):
    try:
        yt = youtube_dl.YoutubeDL(youtube_dl_options)
        v = yt.extract_info(url, download=False)
        return v['title']
    except:
        return False

async def parsePlaylist(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    try:
        page = await aiohttp.post(url, headers=headers)
        page = await page.text()

        #page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page, 'html.parser')
        tags = soup.find_all("tr", class_="pl-video yt-uix-tile ")
        links = []

        for tag in tags:
            links.append("https://www.youtube.com/watch?v=" + tag['data-video-id'])
        if links != []:
            return links
        else:
            return False
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
    elif client.voice.channel != message.author.voice_channel:
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

def isPlaylistValid(data):
    data = [y for y in data if y != ""] # removes all empty elements
    data = [y for y in data if y != "\n"]
    for link in data:
        pattern = "^(https:\/\/www\.youtube\.com\/watch\?v=...........*)|^(https:\/\/youtu.be\/...........*)|^(https:\/\/youtube\.com\/watch\?v=...........*)"
        rr = re.search(pattern, link, re.I | re.U)
        if rr == None:
            return False
    return True

class Playlist():
    def __init__(self, filename=None):
        self.filename = filename
        self.current = 0
        self.stop = False
        self.lastAction = 999
        self.currentTitle = ""
        self.type = filename["type"]
        if filename["type"] == "playlist":
            self.playlist = dataIO.fileIO("playlists/" + filename["filename"] + ".json", "load")["playlist"]
        elif filename["type"] == "queue":
            self.playlist = dataIO.fileIO("json/queue.json", "load")
        elif filename["type"] == "favorites":
            self.playlist = dataIO.fileIO("favorites/" + filename["filename"] + ".json", "load")
        elif filename["type"] == "local":
            self.playlist = filename["filename"]
        elif filename["type"] == "singleSong":
            self.playlist = [filename["filename"]]
            self.playSingleSong(self.playlist[0])
        else:
            raise("Invalid playlist call.")
        if filename["type"] != "singleSong":
            self.nextSong(0)

    def nextSong(self, nextTrack, lastError=False):
        global musicPlayer
        if not self.passedTime() < 1 and not self.stop: #direct control
            if musicPlayer: musicPlayer.stop()
            self.lastAction = int(time.perf_counter())
            try:
                if isPlaylistValid([self.playlist[nextTrack]]): #Checks if it's a valid youtube link
                    if settings["DOWNLOADMODE"]:
                        path = self.getVideo(self.playlist[nextTrack])
                        try:
                            logger.info("Starting track...")
                            musicPlayer = client.voice.create_ffmpeg_player("music/" + path, options='''-filter:a "volume={}"'''.format(settings["VOLUME"]))
                            musicPlayer.start()
                        except:
                            logger.warning("Something went wrong with track " + self.playlist[self.current])
                            if not lastError: #prevents error loop
                                self.lastAction = 999
                            self.nextSong(self.getNextSong(), lastError=True)
                    else: #Stream mode. Buggy.
                        musicPlayer = client.voice.create_ytdl_player(self.playlist[nextTrack], options=youtube_dl_options)
                        musicPlayer.start()
                else: # must be a local playlist then
                    musicPlayer = client.voice.create_ffmpeg_player(self.playlist[nextTrack], options='''-filter:a "volume={}"'''.format(settings["VOLUME"]))
                    musicPlayer.start()
            except Exception as e:
                print("here!")
                logger.warning("Something went wrong with track " + self.playlist[self.current])
                if not lastError: #prevents error loop
                    self.lastAction = 999
                self.nextSong(self.getNextSong(), lastError=True)

    async def songSwitcher(self):
        while not self.stop:
            if musicPlayer.is_done() and not self.stop:
                self.nextSong(self.getNextSong())
            await asyncio.sleep(0.5)

    def playSingleSong(self, url):
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

    def getNextSong(self):
        try:
            song = self.playlist[self.current+1]
            self.current += 1
            return self.current
        except: #if the current song was the last song, returns the first in the playlist
            song = self.playlist[0]
            self.current = 0
            return self.current

    def passedTime(self):
        return abs(self.lastAction - int(time.perf_counter()))

    def pause(self):
        if musicPlayer.is_playing() and not self.stop:
            musicPlayer.pause()

    def resume(self):
        if not self.stop:
            musicPlayer.resume()

    def shuffle(self):
        if not self.stop:
            shuffle(self.playlist)

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

#ADMIN
async def blacklist(message, mode):
    global blacklisted_users
    if isMemberAdmin(message):
        if message.mentions:
            member = message.mentions[0]
        else:
            if len(message.content.split(" ")) >= 2:
                if message.content.startswith("!blacklist"):
                    name = message.content[11:]
                elif message.content.startswith("!forgive"):
                    name = message.content[9:]
                member = discord.utils.get(message.server.members, name=name)
                if member == None:
                    await client.send_message(message.channel, "`User not found.`")
                    return False
            else:
                await client.send_message(message.author, blacklisted_users)
                return False
        if mode == "add":
            blacklisted_users.update({member.id : "True"})
            await client.send_message(message.channel, "`{} is now in blacklist.`".format(member.name))
        elif mode == "remove":
            if member.id in blacklisted_users:
                del blacklisted_users[member.id]
                await client.send_message(message.channel, "`{} has been removed from blacklist.`".format(member.name))
            else:
                await client.send_message(message.channel, "`User not in blacklist.`")
                return False
        else:
            await client.send_message(message.author, blacklisted_users)
            return False
        dataIO.fileIO("json/blacklist.json", "save", blacklisted_users)
    else:
        await client.send_message(message.channel, "`I don't take orders from you.`")

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

def loadProverbs():
    with open("proverbs.txt", encoding='utf-8', mode="r") as f:
        data = f.readlines()
    return data

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
    global proverbs ,imagesList, blacklisted_users
    loadHelp()

    blacklisted_users = dataIO.fileIO("json/blacklist.json", "load")
    logger.info("Loaded " + str(len(blacklisted_users)) + " blacklisted users.")

    proverbs = loadProverbs()
    logger.info("Loaded " + str(len(proverbs)) + " proverbs.")

    imagesList = []
    for f in listdir('twitchimages/'):
        imagesList.append(f)
    logger.info("loaded files.")

def main():
    global settings, logger, client, musicPlayer, currentPlaylist, imagesList, uptime_timer

    logger = loggerSetup()
    dataIO.logger = logger

    loadDataFromFiles()

    uptime_timer = int(time.perf_counter())
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
