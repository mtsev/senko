import re

from discord import Message
from discord.ext.commands import Bot, Cog, Context, group


class Database:
    def __init__(self, wordsfile: str) -> None:
        self.file = wordsfile
        with open(self.file) as fh:
            self.words = fh.read().splitlines()

    def get_words(self) -> list:
        return self.words

    def add_word(self, word: str) -> bool:
        if word not in self.words:
            self.words.append(word)
            self._update()
            return True
        return False

    def del_word(self, word: str) -> bool:
        if word in self.words:
            self.words.remove(word)
            self._update()
            return True
        return False

    def _update(self) -> None:
        with open(self.file, 'w') as fh:
            fh.write("\n".join(self.words))


class Keywords(Cog):
    """
    IRC-style keyword highlighting for word or phrases.
    Will not highlight partial match, only full word or phrase match.
    Highlight is represented as a DM from Senko with a jumplink.
    Currently only OWNER is permitted to use this command.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.keywords = Database('./words.txt')

    @Cog.listener()
    async def on_message(self, message: Message) -> None:

        # Send a DM if keyword is mentioned. Currently only for OWNER.
        user = self.bot.get_user(self.bot.config['owner'])
        assert user is not None
        if message.author != user and message.guild is not None:
            for word in self.keywords.getWords():
                if re.search("(^|\W)" + re.escape(word) + "($|\W)", message.content, re.I):

                    # Ignore keyword if it is nick in IRC bot
                    if f"<{word.lower()}>" in message.content.lower():
                        continue

                    # Escape backticks to avoid breaking output markdown
                    quote = message.clean_content.replace("`", "'")
                    
                    await user.send(
                            f".\n**#{message.channel.name}**  {message.channel.guild}```markdown\n"
                            f"<{message.author.display_name}> {quote}"
                            f"```{message.jump_url}")
                    break

    @group(aliases=['keyword', 'keywords', 'kw'])
    async def notify(self, ctx: Context) -> None:
        # Currently only for OWNER.
        user = self.bot.get_user(self.bot.config['owner'])
        assert user is not None
        if ctx.author != user:
            return

    @notify.group(name='add', aliases=['new'])
    async def notify_add(self, ctx: Context, *args: str) -> None:
        """Add new keywords to list."""
        if len(args) > 0:
            added = []
            for a in args:
                if self.keywords.add_word(a.lower()):
                    added.append(a.lower())
            if len(added) > 0:
                await self._send(ctx, 'Added: ' + ", ".join(added))
            else:
                await self._send(ctx, 'No keywords added.')

    @notify.group(name='rem', aliases=['remove', 'del', 'delete'])
    async def notify_rem(self, ctx: Context, *args: str) -> None:
        """Remove keywords from list."""
        if len(args) > 0:
            removed = []
            for a in args:
                if self.keywords.del_word(a.lower()):
                    removed.append(a.lower())
            if len(removed) > 0:
                await self._send(ctx, 'Removed: ' + ", ".join(removed))
            else:
                await self._send(ctx, 'No keywords removed.')

    @notify.group(name='clear')
    async def notify_clear(self, ctx: Context) -> None:
        """Remove all keywords."""
        old_words = self.keywords.getWords().copy()
        for w in old_words:
            self.keywords.del_word(w)
        if len(old_words) > 0:
            await self._send(ctx, 'Removed: ' + ", ".join(old_words))
        else:
            await self._send(ctx, 'No keywords to remove.')

    @notify.group(name='list')
    async def notify_list(self, ctx: Context) -> None:
        """List all keywords."""
        if len(self.keywords.getWords()) == 0:
            await self._send(ctx, 'You have no keywords.')
        else:
            await self._send(ctx, 'Keywords: ' + ", ".join(self.keywords.getWords()))

    async def _send(self, ctx, message: str) -> None:
        """Send formatted output to Discord."""
        await ctx.author.send(f'{message}')


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Keywords(bot))
