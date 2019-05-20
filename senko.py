#!/usr/bin/env python3
import discord
from discord.ext import commands
import logging
import re

from dice import Dice
from cooldown import CooldownTimer
from keywords import Keywords

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
bot = commands.Bot(command_prefix='!', help_command=None)
dice = Dice(keys['API_KEY'])
dice_cd = CooldownTimer(60, 2, 3)
keywords = Keywords('./words.txt')

# Start up actions
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    dice.roll(1, 6)     # initialise dice cache

# Channel messages actions
@bot.event
async def on_message(message):
    # Ignore own messages
    if message.author == bot.user:
        return

    # Send a DM if keyword is mentioned. Currently only for OWNER.
    user = bot.get_user(int(keys['OWNER_ID']))
    assert user is not None
    if message.author != user and message.guild is not None:
        for word in keywords.words:
            if re.search("(^|\W)" + re.escape(word) + "($|\W)", message.content, re.I):
                quote = message.clean_content.replace("`", "'")
                await user.send(
                        f".\n**#{message.channel.name}**  {message.channel.guild}```markdown\n"
                        f"<{message.author.display_name}> {quote}"
                        f"```{message.jump_url}")
                break

    # Easter egg
    if re.search("(^|\W)i'?m back($|\W)", message.content, re.I):
        await message.channel.send("おかえりなのじゃ！")

    # Re-enable commands after overwriting on_message
    await bot.process_commands(message)


"""
IRC-style keyword highlighting for word or phrases.
Will not highlight partial match, only full word or phrase match.
Highlight is represented as a DM from Senko with a jumplink.
Currently only OWNER is permitted to use this command.
"""
@bot.command()
async def notify(ctx, cmd, *args):
    # Currently only for OWNER.
    user = bot.get_user(int(keys['OWNER_ID']))
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
        await user.send(message)


""" 
Dice roll command using random.org
Given no arguments generates number between 1 and 6 inclusive.
Given one integer i, generates number between (+-)1 and i inclusive.
Given two integers i and j, generates number between i and j inclusive.
Given three integers i, j, and n, generates n numbers between i and j inclusive.
"""
@bot.command()
async def roll(ctx, *args):

    # Non-integer arguments not handled
    try:
        args = [int(x) for x in args]
    except ValueError:
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
                result = args[0]

        # Two arguments
        elif len(args) == 2:
            result = dice.roll(args[0], args[1])

        # Three arguments
        elif len(args == 3):
            result = dice.roll(args[0], args[1], args[2])

        # More than 3 arguments not handled
        else:
            return

    # Send number to discord
    await ctx.send(', '.join(str(x) for x in result))


bot.run(keys['TOKEN'])
