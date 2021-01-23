#!/usr/bin/env python3
import os
import logging

import yaml
from discord.ext.commands import Bot, Context, CommandError, CommandOnCooldown
from discord import Intents

from cogs.utils.logs import log_console


# Import config file
with open('config.yaml') as stream:
    config = yaml.safe_load(stream)

# Set gateway intents
intents = Intents.default()
intents.members = True

# Initialise bot
bot = Bot(command_prefix=config['prefix'], intents=intents)
bot.remove_command('help')
bot.owner = config['owner']
bot.keys = config['keys']
bot.db = config['database']
bot.quiet = config['quiet']
bot.dt = config['dt_channels']

# Load cogs
for file in filter(lambda file: file.endswith('.py'), os.listdir('./cogs')):
    bot.load_extension(f'cogs.{file[:-3]}')

# Log bot startup
@bot.event
async def on_ready() -> None:
    log_console(f'We have logged in as {bot.user} in these servers:')
    for guild in bot.guilds:
        log_console(f'{guild.name} ({guild.id})')
    log_console(f'({len(bot.guilds)} servers)')
    log_console('************************')

# Handle command cooldown
@bot.event
async def on_command_error(ctx: Context, error: CommandError) -> None:
    if isinstance(error, CommandOnCooldown):
        await ctx.send(error)

# Start bot
bot.run(config['token'])