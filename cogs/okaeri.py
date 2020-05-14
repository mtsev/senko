import re

from discord import Message
from discord.ext.commands import Bot, Cog


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


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Okaeri(bot))
