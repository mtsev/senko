#!/usr/bin/env python3
import discord
from discord.ext import commands
import logging
import re

from dice import Dice
from cooldown import CooldownTimer

"""
# Set up logging
log = logging.getLogger('discord')
log.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
log.addHandler(handler)
"""

# Read keys file into dict
keys = {}
with open('./keys.env') as fh:
    for line in fh:
        key, value = line.strip().split('=')
        keys[key] = value.strip()

# Initialise objects
bot = commands.Bot(command_prefix='!')
dice = Dice(keys['API_KEY'])
dice_cd = CooldownTimer(60, 2, 3)


# Start up actions
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    dice.roll(1, 6)     # initialise dice cache


# Channel messages actions
@bot.event
async def on_message(message):
    if message.author == client.user:
        return

    """Easter egg"""
    if re.search("\bi'?m back\b", message.content, re.IGNORECASE):
        await message.channel.send("おかえりなのじゃ！")



""" 
Dice roll command using random.org
Given no arguments generates number between 1 and 6 inclusive.
Given one integer i, generates number between (+-)1 and i inclusive.
Given two integers i and j, generates number between i and j inclusive.
"""
@bot.command()
async def roll(ctx, *args):

    # More than 2 arguments not handled
    if len(args) > 2:
        return

    # Cooldown - max 2 rolls per minute. Silent after 3 warnings. No cd for DMs.
    if ctx.guild is not None:
        # Update the cooldown timer
        dice_cd.update(ctx.author.id)

        # Print cd warning if not silent
        if dice_cd.is_cooldown(ctx.author.id):
            if not dice_cd.is_silent(ctx.author.id):
                await ctx.send(
                    f'Please wait {dice_cd.count(ctx.author.id)} '
                    f'seconds before rolling again.'
                )
            return

    # Roll dice
    try:
        # No arguments
        if len(args) == 0:
            result = dice.roll(1, 6)
        
        # One argument
        elif len(args) == 1:
            if int(args[0]) > 1:
                result = dice.roll(1, int(args[0]))
            elif int(args[0]) < -1:
                result = dice.roll(-1, int(args[0]))
            else:
                result = int(args[0])

        # Two arguments
        else:
            result = dice.roll(int(args[0]), int(args[1]))

    except ValueError:
        return

    # Send number to discord
    await ctx.send(result)


bot.run(keys['TOKEN'])
