#!/usr/bin/env python3
import os
import sys

import yaml
from discord import Intents
from discord.ext.commands import Bot, Context, CommandError, CommandOnCooldown

from utils import log


# Import config file
with open('config.yaml') as stream:
    config = yaml.safe_load(stream)

# Set gateway intents
intents = Intents.none()
intents.guilds = True
intents.members = True
intents.messages = True

# Initialise bot
bot = Bot(command_prefix=config['prefix'], intents=intents)
bot.remove_command('help')
bot.owner = config['owner']
bot.keys = config['keys']
bot.db = config['database']
bot.quiet = config['quiet']
bot.dt = config['dt_channels']

# Load cogs in setup
async def setup_hook() -> None:
    for file in filter(lambda file: file.endswith('.py'), os.listdir('./cogs')):
        await bot.load_extension(f'cogs.{file[:-3]}')

# Log bot startup
@bot.event
async def on_ready() -> None:
    log.console(f'Logged in as {bot.user} in {len(bot.guilds)} servers.')
    owner = bot.get_user(int(config['owner']))
    await owner.send(f'Connected in {len(bot.guilds)} servers.')

# Log bot disconnect
@bot.event
async def on_disconnect() -> None:
    log.console('Disconnected from Discord.')

# Handle command cooldown
@bot.event
async def on_command_error(ctx: Context, error: CommandError) -> None:
    if isinstance(error, CommandOnCooldown):
        await ctx.send(error)

# Start bot
token = config['token_dev'] if len(sys.argv) > 1 else config['token_prod']
bot.run(token)
