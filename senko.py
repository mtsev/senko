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
recent_users = {}

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

        # Cooldown
        if message.author.id in recent_users:
            seconds = recent_users[message.author.id] - time.time()
            if seconds < 60:
                await message.channel.send(f"Please wait {seconds} seconds before rolling again.")
                return
        else:
            recent_users[message.author.id] = time.time()

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
