#!/usr/bin/env python3
import discord
from discord.ext import commands
import logging
import re
import sys

from commands.dice import Dice
from commands.cooldown import CooldownTimer
from commands.keywords import Keywords

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
with open('./keys') as fh:
    for line in fh:
        key, value = line.strip().split('=')
        keys[key] = value.strip()

# Read Discord IDs file into dict
ids = {}
with open('./ids') as fh:
    for line in fh:
        key, value = line.strip().split('=')
        ids[key] = int(value.strip())

# Initialise
bot = commands.Bot(command_prefix='!', help_command=None)
dice = Dice(keys['RANDOM'])
dice_cd = CooldownTimer(60, 2, 3)
image_cd = CooldownTimer(3600, 1, 0)
keywords = Keywords('./words.txt')

# Start up actions
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    dice.roll(1, 6)     # initialise dice cache
    dice.roll(1, 1000)  # initialise d1k cache

# Channel messages actions
@bot.event
async def on_message(message):

    # Ignore self
    if message.author == bot.user:
        return

    # Ignore Ekaterina outside of Test server
    if message.author.id == ids['EKA_ID'] and message.guild.id != ids['EKA_SERVER']:
        return

    # Ignore Magic Conch
    if message.author.id == ids['CONCH_ID']:
        return

    # Send a DM if keyword is mentioned. Currently only for OWNER.
    user = bot.get_user(ids['OWNER_ID'])
    assert user is not None
    if message.author != user and message.guild is not None:
        for word in keywords.words:
            if re.search("(^|\W)" + re.escape(word) + "($|\W)", message.content, re.I):

                # Ignore keyword if it is nick in IRC bot
                if f"<{word.lower()}>" in message.content.lower():
                    continue

                # Escape backticks to avoid breaking output markdown
                quote = message.clean_content.replace("`", "'")
                
                await user.send(
                        f".\n**#{message.channel.name}**  {message.channel.guild}```markdown\n"
                        f"<{message.author.display_name}> {quote}"
                        f"```{message.jump_url}")
                break

    # Commands disabled for certain channels
    if message.channel.id == ids['NO_CMD_CHAN']:
        return
    if message.guild.id == ids['DT_SERVER'] and message.channel.id != ids['DT_SPAM_CHAN']:
        return


    # "Welcome back" greeting, no restrictions
    if re.search("(^|\W)i[‘’']?m back($|\W)", message.content, re.I):
        await message.channel.send("おかえりなのじゃ！")

    # DT spam channel features, unadvertised cooldown
    if message.channel.id == ids['DT_SPAM_CHAN'] or message.channel.id == ids['DT_TEST_CHAN']:
        if re.search("(^|\W)dumb bran($|\W)", message.content, re.I):
            image_cd.update(message.channel.id)
            if not image_cd.is_cooldown(message.channel.id):
                await message.channel.send(file=discord.File('images/dumb_bran.png'))
        
        elif re.search("(^|\W)boi($|\W)", message.content, re.I):
            image_cd.update(message.channel.id)
            if not image_cd.is_cooldown(message.channel.id):
                await message.channel.send(file=discord.File('images/boi.jpg'))

    # Explicitly process commands after overwriting on_message
    ctx = await bot.get_context(message)
    if ctx.valid:
        await bot.invoke(ctx)

"""
IRC-style keyword highlighting for word or phrases.
Will not highlight partial match, only full word or phrase match.
Highlight is represented as a DM from Senko with a jumplink.
Currently only OWNER is permitted to use this command.
"""
@bot.command()
async def notify(ctx, cmd, *args):

    # Currently only for OWNER.
    user = bot.get_user(ids['OWNER_ID'])
    assert user is not None
    if ctx.author != user:
        return

    message = None

    # Add a keyword to list
    if cmd == "add" and len(args) > 0:
        added = []
        for a in args:
            if keywords.add_word(a.lower()):
                added.append(a.lower())
        if len(added) > 0:
            message = "Added: " + ", ".join(added)
        else:
            message = "No keywords added."

    # Remove a keyword from list
    elif cmd == "rem" and len(args) > 0:
        removed = []
        for a in args:
            if keywords.del_word(a.lower()):
                removed.append(a.lower())
        if len(removed) > 0:
            message = "Removed: " + ", ".join(removed)
        else:
            message = "No keywords removed."

    # Remove all keywords from list
    if cmd == "clear":
        old_words = keywords.words.copy()
        for w in old_words:
            keywords.del_word(w)
        if len(old_words) > 0:
            message = "Removed: " + ", ".join(old_words)
        else:
            message = "No keywords to remove."

    # Print out keywords list
    elif len(keywords.words) == 0:
        message = "You have no keywords."
    elif cmd == "list":
        message = "Keywords: " + ", ".join(keywords.words)

    if message is not None:
        await user.send(f'```{message}```')


""" 
Dice roll command using random.org
Given no arguments, generates number between 1 and 6 inclusive.
Given one integer i, generates number between (+-)1 and i inclusive.
Given two integers i and j, generates number between i and j inclusive.
Given three integers i, j, and n, generates n numbers between i and j inclusive.
"""
@bot.command()
async def roll(ctx, *args):

    # More than 3 arguments not handled
    if len(args) > 3:
        return

    # Non-integer arguments not handled
    try:
        args = [int(x) for x in args]
    except ValueError:
        return

    # Cooldown - max 2 rolls per minute. Silent after 3 warnings. No cd for DMs.
    if ctx.guild is not None and ctx.channel.id != ids['NO_CD_CHAN']:
        # Update the cooldown timer
        dice_cd.update(ctx.author.id)

        # Print cd warning if not silent
        if dice_cd.is_cooldown(ctx.author.id):
            if not dice_cd.is_silent(ctx.author.id):
                await ctx.send(
                        f'Please wait {dice_cd.count(ctx.author.id)} '
                        f'seconds before rolling again.')
            return

    # Roll dice
    async with ctx.typing():
        # No arguments
        if len(args) == 0:
            result = dice.roll(1, 6)
        
        # One argument
        elif len(args) == 1:
            if args[0] > 1:
                result = dice.roll(1, args[0])
            elif args[0] < -1:
                result = dice.roll(-1, args[0])
            else:
                result = [args[0]]

        # Two arguments
        elif len(args) == 2:
            result = dice.roll(args[0], args[1])

        # Three arguments
        else:
            result = dice.roll(args[0], args[1], args[2])

    # Send number to discord
    message = ', '.join(str(x) for x in result)
    if len(message) > 2000:
        await ctx.send("Your roll is too big for Discord.")
    elif len(message) > 250:
        await ctx.send("Your roll has been sent as a DM.")
        await ctx.author.send(message)
    else:
        await ctx.send(message)


bot.run(keys['TOKEN'])
