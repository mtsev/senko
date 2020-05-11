import re

from discord import Message
from discord.ext.commands import *

class Okaeri(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.channel.id in self.bot.config['quiet_channels']:
            return
            
        if re.search("(^|\W)i[‘’']?m back($|\W)", message.content, re.I):
            await message.channel.send("おかえりなのじゃ！")


def setup(bot: Bot) -> None:
    bot.add_cog(Okaeri(bot))
