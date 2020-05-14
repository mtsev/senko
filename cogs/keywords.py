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

    def get_guild(self, guild: int) -> dict:
        # If guild isn't in cache, update cache
        if guild not in self.cache.keys():
            with self.conn.cursor() as cursor:
                query = "CALL get_words (%s)"
                cursor.execute(query, (guild,))
                results = cursor.fetchall()
            self.cache.add_guild(guild, results)

        # Return guild from cache
        return self.cache.get_guild(guild)

    def get_words(self, user: int) -> list:
        if self.cache.has_user(user):
            words = self.cache.get_words(user)
        
        # If user isn't in cache, get from database
        else:
            with self.conn.cursor() as cursor:
                query = "SELECT `word` FROM `keywords` WHERE `user`=%s"
                cursor.execute(query, (user,))
                results = cursor.fetchall()
            words = [r['word'] for r in results]

        return words

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
        self.keywords = Database(bot.db)

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        # Ignore DMs
        if message.guild is None:
            return

        # Get all users and their words in guild
        words = self.keywords.get_guild(message.guild.id)
        for user_id in words.keys():

            # Ignore messages from the user themselves
            if message.author.id == int(user_id):
                continue

            # Send notification if any words match
            for word in words[user_id]:
                if re.search("(^|\W)" + re.escape(word) + "($|\W)", message.content, re.I):
                    await self._send_notification(int(user_id), message)
                    break

    async def _send_notification(self, user_id: int, message: Message) -> None:
        # Get user to send message to
        user = self.bot.get_user(user_id)

        # Escape backticks to avoid breaking output markdown
        quote = message.clean_content.replace("`", "'")
        
        # Send DM to user
        await user.send(
            f".\n**#{message.channel.name}**  {message.channel.guild}```markdown\n"
            f"<{message.author.display_name}> {quote}"
            f"```{message.jump_url}")

    @group(aliases=['keyword', 'keywords', 'kw'])
    async def notify(self, ctx: Context) -> None:
        pass

    @notify.group(name='add', aliases=['new'])
    async def notify_add(self, ctx: Context, *args: str) -> None:
        """Add new keywords to list."""
        log_command(ctx)
        words = [a.lower() for a in args]
        self.keywords.add_words(ctx.author.id, words)
        words = self.keywords.get_words(ctx.author.id)
        await self._send(ctx, words)

    @notify.group(name='rem', aliases=['remove', 'del', 'delete'])
    async def notify_rem(self, ctx: Context, *args: str) -> None:
        """Remove keywords from list."""
        log_command(ctx)
        words = [a.lower() for a in args]
        self.keywords.remove_words(ctx.author.id, words)
        words = self.keywords.get_words(ctx.author.id)
        await self._send(ctx, words)
        
    @notify.group(name='clear')
    async def notify_clear(self, ctx: Context) -> None:
        """Remove all keywords."""
        log_command(ctx)
        words = self.keywords.get_words(ctx.author.id)
        self.keywords.remove_words(ctx.author.id, words)
        words = self.keywords.get_words(ctx.author.id)
        await self._send(ctx, words)

    @notify.group(name='list')
    async def notify_list(self, ctx: Context) -> None:
        """List all keywords."""
        log_command(ctx)
        words = self.keywords.get_words(ctx.author.id)
        await self._send(ctx, words)

    async def _send(self, ctx, words: list) -> None:
        """Send formatted output to Discord."""
        if not words:
            message = 'You have no keywords.'
        else:
            message = 'Keywords: ' + ', '.join(words)
        await ctx.author.send(f'```{message}```')

def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Keywords(bot))
