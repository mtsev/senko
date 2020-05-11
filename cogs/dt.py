import re

from discord import File, Message
from discord.ext.commands import *

class DT(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.channel.id not in self.bot.config['dt_channels']:
            return
            
        if re.search("(^|\W)dumb bran($|\W)", message.content, re.I):
            await message.channel.send(file=File('images/dumb_bran.png'))
        
        elif re.search("(^|\W)boi($|\W)", message.content, re.I):
            await message.channel.send(file=File('images/boi.jpg'))


def setup(bot: Bot) -> None:
    bot.add_cog(DT(bot))
