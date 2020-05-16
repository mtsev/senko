import re

import pymysql.cursors
from discord import Guild, Member, Message
from discord.ext.commands import Bot, Cog, Context, group

from .utils.logs import *
from .utils.cache import Cache


class Database:
    def __init__(self, db) -> None:
        self.conn = pymysql.connect(
            unix_socket = db['socket'],
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

    def add_guild(self, guild: Guild) -> None:
        # This gets called when Senko joins a new guild. Don't add to cache.
        # Get all existing users.
        with self.conn.cursor() as cursor:
            query = "SELECT DISTINCT `user` FROM `keywords`"
            cursor.execute(query)
            results = cursor.fetchall()
        all_users = [r['user'] for r in results]

        # Add new guild mapping for users who are in this guild
        with self.conn.cursor() as cursor:
            for member in guild.members:
                if str(member.id) in all_users:
                    query = "INSERT INTO `guilds` (`guild`, `user`) VALUES (%s, %s)"
                    cursor.execute(query, (guild.id, member.id))
        self.conn.commit()

    def remove_guild(self, guild: Guild) -> None:
        # Remove guild mappings from database and cache
        with self.conn.cursor() as cursor:
            query = "DELETE FROM `guilds` WHERE `guild`=%s"
            cursor.execute(query, (guild.id,))
        self.conn.commit()
        self.cache.remove_guild(guild.id)

    def add_guild_member(self, guild: int, member: int) -> None:
        # This gets called when someone joins a guild that Senko is in.
        with self.conn.cursor() as cursor:
            query = "SELECT DISTINCT `user` FROM `keywords`"
            cursor.execute(query)
            results = cursor.fetchall()
        all_users = [r['user'] for r in results]

        # If the member is a user, add new guild mapping in database and
        # update cache if the guild is in cache.
        if str(member) in all_users:
            with self.conn.cursor() as cursor:
                query = "INSERT INTO `guilds` (`guild`, `user`) VALUES (%s, %s)"
                cursor.execute(query, (guild, member))
            self.conn.commit()
            self.cache.add_guild_member(guild, member)

    def remove_guild_member(self, guild: int, member: int) -> None:
        # This gets called when someone leave a guild that Senko is in.
        # Don't need to check if this guild-user mapping actually exists.
        with self.conn.cursor() as cursor:
            query = "DELETE FROM `guilds` WHERE `guild`=%s AND `user`=%s"
            cursor.execute(query, (guild, member))
        self.conn.commit()
        self.cache.remove_guild_member(guild, member)

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

        # If the user is cached, we need to add the words to cache too.
        if self.cache.has_user(user):
            self.cache.add_words(user, words)

    def remove_words(self, user: int, words: list) -> None:
        # Remove words from database
        with self.conn.cursor() as cursor:
            for word in words:
                query = "DELETE FROM `keywords` WHERE `user`=%s AND `word`=%s"
                cursor.execute(query, (user, word))
        self.conn.commit()

        # Update cache
        self.cache.remove_words(user, words)

    def is_new_user(self, user: int) -> bool:
        # Check if a user is in database or not. Check cache first.
        if self.cache.has_user(user):
            return False
        with self.conn.cursor() as cursor:
            query = "SELECT EXISTS (SELECT 1 FROM `guilds` WHERE `user`=%s)"
            cursor.execute(query, (user,))
            result = cursor.fetchone()
        return (0 in result.values())

    def add_new_user(self, guilds: list, user: int) -> None:
        # This only gets called after is_new_user() so we know the user is new.
        # Add all the guild mappings to database and add new user to cache.
        with self.conn.cursor() as cursor:
            for guild in guilds:
                query = "INSERT INTO `guilds` (`guild`, `user`) VALUES (%s, %s)"
                cursor.execute(query, (guild, user))
        self.conn.commit()
        self.cache.add_user(guilds, user)


class Keywords(Cog):
    """
    IRC-style keyword highlighting for word or phrases.
    Won't highlight partial word match, only full word or phrase match.
    Highlight is represented as a DM from Senko with a jumplink.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.keywords = Database(bot.db)

    @Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        print(f'{member.display_name} joined {member.guild.name}')
        self.keywords.add_guild_member(member.guild.id, member.id)

    @Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        print(f'{member.display_name} left {member.guild.name}')
        self.keywords.remove_guild_member(member.guild.id, member.id)

    @Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        print(f'Joined new server {guild.name}')
        self.keywords.add_guild(guild)

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        print(f'Removed from server {guild.name}')
        self.keywords.remove_guild(guild)

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

            # Check if user is in the channel that the message was sent in
            if int(user_id) not in [m.id for m in message.channel.members]:
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

        # This could potentially be a member's first time adding words.
        # Then we want to also add their guild mappings to database.
        if self.keywords.is_new_user(ctx.author.id):
            print(f'Adding new user {ctx.author.display_name} to database')
            guilds = [g.id for g in self.bot.guilds if g.get_member(ctx.author.id) is not None]
            self.keywords.add_new_user(guilds, ctx.author.id)

        # Then we'll add the words for this user
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
