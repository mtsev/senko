import re

from discord import Message
from discord.ext.commands import Bot, Cog, command

from .utils.logs import *


class Okaeri(Cog):
    """Welcome back."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.guild and message.guild.id in self.bot.quiet['guilds']:
            return
        if message.channel.id in self.bot.quiet['channels']:
            return

        if re.search("(^|\W)i[‘’']?m back($|\W)", message.content, re.I):
            await message.channel.send("おかえりなのじゃ！")

    # @command(aliases=['quiet'])
    # async def mute(self, ctx: Context, *args: str) -> None:
    #     log_command(ctx)
    #     if not args:
    #         guild = ctx.guild.id
    #         muted = self.bot.quiet['guilds']
    #         if (guild not in muted):
    #             muted.append(ctx.guild.id)
    #             print(f'Added guild: {muted[-1]}')

    #     else:
    #         for arg in args:
    #             search = [x for x in ctx.guild.channels if x.name == arg]
    #             channel = next(iter(search), None)
    #             muted = self.bot.quiet['channels']
    #             if channel is not None and channel not in muted:
    #                 muted.append(channel.id)
    #                 print(f'Added channel: {muted[-1]}')


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Okaeri(bot))
