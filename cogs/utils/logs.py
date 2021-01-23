from discord.ext.commands import Context
import logging

log = logging.getLogger(__name__)

def log_command(ctx: Context) -> None:
    if ctx.guild:
        channel = f'{ctx.guild}/{ctx.channel}'
    else:
        channel = 'DM'
    log.warning(f'({channel}) <{ctx.author}> {ctx.message.content}')
