#!/usr/bin/env python3
import discord
import logging

from .commands.dice import Dice

# Set up logging
log = logging.getLogger('discord')
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='senko.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
log.addHandler(handler)

# Read keys file into dict
keys = {}
with open('./keys.env') as fh:
    for line in fh:
        key, value = line.strip().split('=')
        keys[key] = value.strip()

# Initialise objects
client = discord.Client()
dice = Dice(keys['API_KEY'])

# Start up actions
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

# Channel messages
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    """ 
    Dice roll command using random.org
    Given no arguments generates number between 1 and 6 inclusive.
    Given one integer i, generates number between 1 and i inclusive.
    Given two integers i and j, generates number between i and j inclusive.
    Given more than three arguments, rolls on first two if they are integers.
    """
    if message.content.startswith('!roll '):
        args = message.content.split(' ')

        try:
            if len(args) == 1:
                result = dice.roll(1, 6)
            elif len(args) == 2:
                result = dice.roll(1, int(args[1]))
            else:
                result = dice.roll(int(args[1]), int(args[2]))

        except ValueError:
            return

        await message.channel.send(result)

client.run(keys['TOKEN'])