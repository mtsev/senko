#!/usr/bin/env python3
import os
import logging

import yaml
from discord.ext.commands import Bot, Context, CommandError, CommandOnCooldown
from discord import Intents

# create logger
log = logging.getLogger(__package__)
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('../senko.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(asctime)s] %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(fh)
log.addHandler(ch)


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
    log.warning(f'We have logged in as {bot.user} in these servers:')
    for guild in bot.guilds:
        log.warning(f'{guild.name} ({guild.id})')
    log.warning(f'({len(bot.guilds)} servers)')
    log.warning('************************')

# Handle command cooldown
@bot.event
async def on_command_error(ctx: Context, error: CommandError) -> None:
    if isinstance(error, CommandOnCooldown):
        await ctx.send(error)

# Start bot
bot.run(config['token'])