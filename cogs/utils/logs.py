from discord.ext.commands import Context

def log_command(ctx: Context) -> None:
    if ctx.guild:
        channel = f'{ctx.guild}/{ctx.channel}'
    else:
        channel = 'DM'
    print(f'({channel}) <{ctx.author}> {ctx.message.content}')
