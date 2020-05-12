from discord import DMChannel, TextChannel
from discord.ext.commands import Context

def log_command(ctx: Context) -> None:
    if isinstance(ctx.channel, TextChannel):
        channel = f'{ctx.channel.guild}/{ctx.channel}'
    elif isinstance(ctx.channel, DMChannel):
        channel = 'DM'
    else:
        channel = 'Unknown'
    print(f'({channel}) <{ctx.author}> {ctx.message.content}')