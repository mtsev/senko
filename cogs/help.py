from discord.ext.commands import Bot, Cog, Context, group

from .utils.logs import *


class Help(Cog):
    """
    Help command.
    """
    # TODO: this is hardcoded, make it dynamic

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @group(aliases=['commands'])
    async def help(self, ctx: Context) -> None:
        log_command(ctx)
        if ctx.invoked_subcommand is None:
            output = ("Keyword notification commands:\n"
                    "  !notify add <keywords>...\n"
                    "  !notify rem <keywords>...\n"
                    "  !notify list\n"
                    "  !notify clear\n\n"
                    "Other commands:\n"
                    "  !roll [<max> [<min> [<num>]]]\n\n"
                    "For more info on a command, type '!help <command>'\n\n")
            await ctx.send(f'```{output}```\nPlease visit our support server if you have any problems or questions: discord.com/invite/39mHBQh')

    @help.group(aliases=['keyword', 'keywords', 'kw'], invoke_without_command=True)
    async def notify(self, ctx: Context) -> None:
        output = ("!notify <subcommand> [arguments]\n\n"
                  "Aliases: keyword, keywords, kw\n\n"
                  "Receive a DM notification from Senko for server messages "
                  "containing your keywords or phrases.\n\n"
                  "Subcommands: add, rem, list, clear\n\n"
                  "For more info on a subcommand, type '!help notify <subcommand>'")
        await ctx.send(f'```{output}```')

    @notify.command(name='add', aliases=['new'])
    async def notify_add(self, ctx: Context) -> None:
        output = ("!notify add <keywords>...\n\n"
                  "Aliases: new\n\n"
                  "Add new keywords or phrases to be notified of. "
                  "Takes one or more keywords and/or phrases as arguments. "
                  "Surround phrases with quotation marks.")
        await ctx.send(f'```{output}```')

    @notify.command(name='rem', aliases=['remove', 'del', 'delete'])
    async def notify_rem(self, ctx: Context) -> None:
        output = ("!notify rem <keywords>...\n\n"
                  "Aliases: remove, del, delete\n\n"
                  "Remove keywords or phrases from notification list. "
                  "Takes one or more keywords and/or phrases as arguments. "
                  "Surround phrases with quotation marks.")
        await ctx.send(f'```{output}```')

    @notify.command(name='list', aliases=['all'])
    async def notify_list(self, ctx: Context) -> None:
        output = ("!notify list\n\n"
                  "Aliases: all\n\n"
                  "See all keywords and phrases in notification list.")
        await ctx.send(f'```{output}```')

    @notify.command(name='clear')
    async def notify_all(self, ctx: Context) -> None:
        output = ("!notify list\n\n"
                  "Remove all keywords and phrases from notification list.")
        await ctx.send(f'```{output}```')

    @help.group()
    async def roll(self, ctx: Context) -> None:
        output = ("!roll [<max> [<min> [<num>]]]\n\n"
                  "Roll dice. Takes up to three arguments.\n\n"
                  "Arguments:\n"
                  "  max  upper bound of range  [default: 6]\n"
                  "  min  lower bound of range  [default: 1]\n"
                  "  num  number of rolls       [default: 1]")
        await ctx.send(f'```{output}```')


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Help(bot))
