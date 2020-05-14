import re

import pymysql.cursors
from discord import Message
from discord.ext.commands import Bot, Cog, Context, group

from .utils.logs import *
from .utils.cache import Cache


class Database:
    def __init__(self, db) -> None:
        self.conn = pymysql.connect(
            host = db['host'],
            port = db['port'],
            user = db['user'],
            password = db['password'],
            db = db['database'],
            charset = 'utf8mb4',
            cursorclass = pymysql.cursors.DictCursor)
        self.cache = Cache(5)

    def get_words(self, guild: int) -> list:
        # If guild isn't in cache, update cache
        if guild not in self.cache.keys():
            with self.conn.cursor() as cursor:
                query = "CALL get_words (%s)"
                cursor.execute(query, (guild,))
                results = cursor.fetchall()
            self.cache.add_guild(guild, results)

        # Return guild from cache
        return self.cache.get_guild(guild)

    def add_words(self, user: int, words: list) -> None:
        # Add words to database
        with self.conn.cursor() as cursor:
            for word in words:
                try:
                    query = "INSERT INTO `keywords` (`user`, `word`) VALUES (%s, %s)"
                    cursor.execute(query, (user, word))
                except pymysql.err.IntegrityError as err:
                    # This error gets thrown if user tries to insert a keyword
                    # they already have (unique key 'unique_keyword'). But if
                    # it's something else, print the error.
                    if 'unique_keyword' not in str(err):
                        print(err)
        self.conn.commit()

        # If the user is already in cache, we only need to add the words
        if self.cache.has_user(user):
            self.cache.add_words(user, words)

        # Otherwise we need to get a list of all the guilds the user is in
        # and add the new user to cache
        else:
            with self.conn.cursor() as cursor:
                query = "SELECT `guild` FROM `guilds` WHERE `user`=%s"
                cursor.execute(query, (user,))
                results = cursor.fetchall()
            guilds = [r['guild'] for r in results]
            self.cache.add_user(user, guilds, words)

    def remove_words(self, user: int, words: list) -> None:
        # Remove words from database
        with self.conn.cursor() as cursor:
            for word in words:
                query = "DELETE FROM `keywords` WHERE `user`=%s AND `word`=%s"
                cursor.execute(query, (user, word))
        self.conn.commit()

        # Update cache
        self.cache.remove_words(user, words)


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
            for word in self.keywords.get_words():
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
            log_command(ctx)
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
            log_command(ctx)
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
        log_command(ctx)
        old_words = self.keywords.get_words().copy()
        for w in old_words:
            self.keywords.del_word(w)
        if len(old_words) > 0:
            await self._send(ctx, 'Removed: ' + ", ".join(old_words))
        else:
            await self._send(ctx, 'No keywords to remove.')

    @notify.group(name='list')
    async def notify_list(self, ctx: Context) -> None:
        """List all keywords."""
        log_command(ctx)
        if len(self.keywords.get_words()) == 0:
            await self._send(ctx, 'You have no keywords.')
        else:
            await self._send(ctx, 'Keywords: ' + ", ".join(self.keywords.get_words()))

    async def _send(self, ctx, message: str) -> None:
        """Send formatted output to Discord."""
        await ctx.author.send(f'{message}')


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Keywords(bot))
