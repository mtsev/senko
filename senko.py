#!/usr/bin/env python3
import discord
import logging
import time

from dice import Dice

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

    """Easter egg"""
    if message.content.startswith("I'm back"):
        await message.channel.send("おかえりなのじゃ！")

    """ 
    Dice roll command using random.org
    Given no arguments generates number between 1 and 6 inclusive.
    Given one integer i, generates number between (+-)1 and i inclusive.
    Given two integers i and j, generates number between i and j inclusive.
    """
    if message.content.startswith('!roll'):

        # Parse arguments
        args = message.content.split(' ')
        if args[0] != '!roll' or len(args) > 3:
            return

        # Cooldown - max 2 rolls per minute, none for DM. Silent after 3 warnings
        if not isinstance(message.channel, discord.DMChannel):
            seconds = int(time.time() - recent_time.get(message.author.id, 0))

            # Over 60 seconds since last roll
            if seconds > 60:
                recent_time[message.author.id] = time.time()
                recent_count[message.author.id] = 1

            # Less than 2 rolls in this minute
            elif recent_count.get(message.author.id, 0) < 2:
                recent_time[message.author.id] = time.time()
                recent_count[message.author.id] += 1

            # More than 3 cooldown warnings
            elif recent_count[message.author.id] < 5:
                recent_count[message.author.id] += 1
                await message.channel.send(f"Please wait {60 - seconds} seconds before rolling again.")
                return

            # Silent after 3 warnings
            else:
                return

        # Roll dice
        try:
            # No arguments
            if len(args) == 1:
                result = dice.roll(1, 6)
            
            # One argument
            elif len(args) == 2:
                if int(args[1]) > 1:
                    result = dice.roll(1, int(args[1]))
                elif int(args[1]) < -1:
                    result = dice.roll(-1, int(args[1]))
                else:
                    result = int(args[1])

            # Two arguments
            else:
                result = dice.roll(int(args[1]), int(args[2]))

        except ValueError:
            return

        # Send message to discord
        await message.channel.send(result)


client.run(keys['TOKEN'])
