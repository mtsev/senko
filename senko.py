#!/usr/bin/env python3
import yaml
import os

from discord.ext.commands import Bot, Context, CommandError, CommandOnCooldown

# Import config file
with open('config.yaml') as stream:
    config = yaml.safe_load(stream)

# Initialise bot
bot = Bot(command_prefix=config['prefix'], help_command=None)
bot.config = config
bot.keys = config['keys']

# Load cogs
for file in filter(lambda file: file.endswith('.py'), os.listdir('./cogs')):
    bot.load_extension(f'cogs.{file[:-3]}')

# Log bot startup
@bot.event
async def on_ready() -> None:
    print(f'We have logged in as {bot.user}')

# Handle command cooldown
@bot.event
async def on_command_error(ctx: Context, error: CommandError) -> None:
    if isinstance(error, CommandOnCooldown):
        await ctx.send(error)

# Start bot
bot.run(config['token'])
