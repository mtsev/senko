from discord.ext.commands import Context
import logging

# create logger
log = logging.getLogger(__name__)
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


def log_command(ctx: Context) -> None:
    # log the usage of commands to log file
    if ctx.guild:
        channel = f'{ctx.guild}/{ctx.channel}'
    else:
        channel = 'DM'
    log.debug(f'({channel}) <{ctx.author}> {ctx.message.content}')


def log_debug(msg: str) -> None:
    # log debug message to log file
    log.debug(msg)


def log_console(msg: str) -> None:
    # log message to console
    log.warning(msg)
