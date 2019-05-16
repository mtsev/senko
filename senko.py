#!/usr/bin/env python3
import discord
import logging
import time

from commands.dice import Dice

# Set up logging
log = logging.getLogger('discord')
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
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
recent_time = {}
recent_count = {}

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
    if message.content.startswith('!roll'):

        # Parse arguments
        args = message.content.split(' ')
        if args[0] != '!roll' or len(args) > 3:
            return

        # Cooldown - max 3 rolls per minute, none for DM. Silent after 5 warnings
        if not isinstance(message.channel, discord.DMChannel):
            seconds = int(time.time() - recent_time.get(message.author.id, 0))
            if seconds > 60:
                recent_time[message.author.id] = time.time()
                recent_count[message.author.id] = 1
            elif recent_count.get(message.author.id, 0) < 3:
                recent_time[message.author.id] = time.time()
                recent_count[message.author.id] += 1
            elif recent_count[message.author.id] < 8:
                await message.channel.send(f"Please wait {60 - seconds} seconds before rolling again.")
                return

        # Roll dice
        try:
            if len(args) == 1:
                result = dice.roll(1, 6)
            elif len(args) == 2:
                if int(args[1]) == 1:
                    result = 1
                else:
                    result = dice.roll(1, int(args[1]))
            elif int(args[1]) == int(args[2]):
                result = int(args[1])
            else:
                result = dice.roll(int(args[1]), int(args[2]))
        except ValueError:
            return

        await message.channel.send(result)

client.run(keys['TOKEN'])
