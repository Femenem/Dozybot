#!/usr/bin/env python3
import discord
from random import randint
from botconfig import *

client = discord.Client()
client.login(botEmail, botPassword)

@client.event
def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!help'):
        client.send_message(message.channel, """You can use these commands:
**Images:**
!4head
!bible
!bot
!camera
!kappa
!bigkappa = the big version
!opie

**Random chance:**
!coin = flip a coin
!roll *number* = roll a random number between 0 and the number specified.

**Utility:**
!dbotjoin *link* = Make this bot join the linked server.
!hello = replies a greeting and your name
!help = list the commands
!servers = list the servers this bot is on
!ts = teamspeak IP address

**Fun:**
!liu = da best
!whats up = obvious
        """)
    #Images
    if '!4head' in message.content:
        client.send_file(message.channel, './images/4Head.png')

    if '!bible' in message.content:
        client.send_file(message.channel, './images/BibleThump.png')

    if '!bot' in message.content:
        client.send_file(message.channel, './images/MrDestructoid.png')

    if '!camera' in message.content:
        client.send_file(message.channel, './images/TTours.png')

    if '!kappa' in message.content:
        client.send_file(message.channel, './images/Kappa.png')

    if '!bigkappa' in message.content:
        client.send_file(message.channel, './images/Kappahd.png')

    if '!opie' in message.content:
        client.send_file(message.channel, './images/OpieOP.png')

    #Random functions
    if message.content.startswith('!coin'):
        roll = randint(0, 1)
        if (roll == 0):
            coin = "heads"
        elif (roll == 1):
            coin = "tails"
        client.send_message(message.channel, '{} flipped a coin and it landed on '.format(message.author.mention()) + coin)

    if message.content.startswith('!roll'):
        rollMax = message.content[6:]
        if rollMax == '':
            rollMax = '100'
        roll = randint(0, int(rollMax))
        client.send_message(message.channel, '{} rolled a '.format(message.author.mention()) + str(roll))

    # Utility
    if message.content.startswith('!hello') or message.content.startswith('!Hello'):
        greetings = ['Hello', 'Greetings', 'Hi', 'Hey there', 'Salutations', 'Howdy', 'What\'s up', 'How\'s it hanging']
        greeting = greetings[randint(0, len(greetings)-1)]
        client.send_message(message.channel, greeting + ' {}!'.format(message.author.mention()))

    if message.content.startswith('!servers'):
        servers = []
        for server in client.servers:
            servers.insert(0 , server.name)
        client.send_message(message.channel, ', '.join(servers))

    if message.content.startswith('!ts'):
        client.send_message(message.channel, 'Teamspeak IP: 88.202.226.151:7297')

    if message.content.startswith('!dbotjoin '):
        inviteLink = message.content[10:]
        client.accept_invite(inviteLink)

    # Fun stuff
    if message.content.startswith('!liu'):
        liu = discord.utils.find(lambda m: m.id == '105714564930260992', message.channel.server.members)
        if (liu == None):
            client.send_message(message.channel, 'Liu is not on this server, but if he was I would call him the best person in the universe.')
        else:
            client.send_message(message.channel, '{} is the greatest person in the universe.'.format(liu.mention()) , mentions=True)

    if message.content.startswith('!whats up'):
        client.send_message(message.channel, 'The sky.')


@client.event
def on_ready():
    print('API version: ' + discord.__version__)
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

client.run()
