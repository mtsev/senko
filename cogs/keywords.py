import re

import pymysql.cursors
from discord import Guild, Member, Message, Forbidden
from discord.ext.commands import Bot, Cog, Context, group

from .utils.logs import log_command, log_console, log_debug
from .utils.cache import Cache


class Database:
    def __init__(self, db) -> None:
        self.conn = pymysql.connect(
            unix_socket = db['socket'],
            user = db['user'],
            password = db['password'],
            db = db['database'],
            charset = 'utf8mb4',
            cursorclass = pymysql.cursors.DictCursor
        )
        self.cache = Cache(5)

    def get_guild(self, guild: int) -> dict:
        """ Return dict of users (user IDs) in a guild and their keywords """
        # If guild isn't in cache, update cache
        if guild not in self.cache.keys():
            self.conn.ping(reconnect=True)
            with self.conn.cursor() as cursor:
                query = "CALL get_words (%s)"
                cursor.execute(query, (guild,))
                results = cursor.fetchall()
            self.cache.add_guild(guild, results)

        # Return guild from cache
        return self.cache.get_guild(guild)

    def add_guild(self, guild: Guild) -> None:
        """ Add guild to database """
        # This gets called when Senko joins a new guild. Don't add to cache.
        # Get all existing users.
        self.conn.ping(reconnect=True)
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
        """ Remove guild mappings from database and cache """
        self.conn.ping(reconnect=True)
        with self.conn.cursor() as cursor:
            query = "DELETE FROM `guilds` WHERE `guild`=%s"
            cursor.execute(query, (guild.id,))
        self.conn.commit()
        self.cache.remove_guild(guild.id)

    def add_guild_member(self, guild: int, member: int) -> None:
        # This gets called when someone joins a guild that Senko is in.
        # If member is an existing user, add new guild mapping in database.
        if not self.is_new_user(member):
            self.conn.ping(reconnect=True)
            with self.conn.cursor() as cursor:
                query = "INSERT INTO `guilds` (`guild`, `user`) VALUES (%s, %s)"
                cursor.execute(query, (guild, member))
            self.conn.commit()
            self.cache.add_guild_member(guild, member)

            # Update cache if the guild is in cache.
            if self.cache.has_user(member):
                self.cache.add_guild_member(guild, member)

            # If the user isn't already in cache, we need to add them.
            else:
                words = self.get_words(member)
                self.cache.add_user([guild], member, words)

    def remove_guild_member(self, guild: int, member: int) -> None:
        # This gets called when someone leave a guild that Senko is in.
        # Don't need to check if this guild-user mapping actually exists.
        self.conn.ping(reconnect=True)
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
            self.conn.ping(reconnect=True)
            with self.conn.cursor() as cursor:
                query = "SELECT `word` FROM `keywords` WHERE `user`=%s"
                cursor.execute(query, (user,))
                results = cursor.fetchall()
            words = [r['word'] for r in results]
        return words

    def add_words(self, user: int, words: list) -> None:
        # Add words to database
        self.conn.ping(reconnect=True)
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
                        log_console(err)
        self.conn.commit()

        # If the user is cached, we need to add the words to cache too.
        if self.cache.has_user(user):
            self.cache.add_words(user, words)

    def remove_words(self, user: int, words: list) -> None:
        """ Remove words from database """
        self.conn.ping(reconnect=True)
        with self.conn.cursor() as cursor:
            for word in words:
                query = "DELETE FROM `keywords` WHERE `user`=%s AND `word`=%s"
                cursor.execute(query, (user, word))
        self.conn.commit()

        # Update cache
        self.cache.remove_words(user, words)

    def is_new_user(self, user: int) -> bool:
        """ Check if a user is in database or not. Check cache first. """
        if self.cache.has_user(user):
            return False
        self.conn.ping(reconnect=True)
        with self.conn.cursor() as cursor:
            query = "SELECT EXISTS (SELECT 1 FROM `guilds` WHERE `user`=%s)"
            cursor.execute(query, (user,))
            result = cursor.fetchone()
        return (0 in result.values())

    def add_new_user(self, guilds: list, user: int) -> None:
        """ Add all the guild mappings to database and add new user to cache. """
        # This only gets called after is_new_user() so we know the user is new.
        self.conn.ping(reconnect=True)
        with self.conn.cursor() as cursor:
            for guild in guilds:
                query = "INSERT INTO `guilds` (`guild`, `user`) VALUES (%s, %s)"
                cursor.execute(query, (guild, user))
        self.conn.commit()
        self.cache.add_user(guilds, user, [])


class Keywords(Cog):
    """
    IRC-style keyword highlighting for word or phrases.
    Won't highlight partial word match, only full word or phrase match.
    Highlight is represented as a DM from Senko with a jumplink.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.keywords = Database(bot.db)

    def _clean_mentions(self, message: str) -> str:
        # remove the ! or & in mentions
        if message:
            return re.sub(r"<@[!&]?([\d]+)>", r"<@\1>", message)
        else:
            return ""

    def _has_word(self, word: str, message: str) -> bool:
        return re.search(r"\b" + re.escape(word) + r"\b", self._clean_mentions(message), re.I)

    @Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        # log_debug(f'{member.display_name} joined {member.guild.name}')
        self.keywords.add_guild_member(member.guild.id, member.id)

    @Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        # log_debug(f'{member.display_name} left {member.guild.name}')
        self.keywords.remove_guild_member(member.guild.id, member.id)

    @Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        log_console(f'Joined new server {guild.name} ({guild.id})')
        self.keywords.add_guild(guild)

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        log_console(f'Removed from server {guild.name} ({guild.id})')
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

            # Send notification if any words match in message or embed
            await self._notif_loop(user_id, words[user_id], message)
            

    async def _notif_loop(self, user_id: str, keywords: list, message: Message) -> None:
        for word in keywords:
            if self._has_word(word, message.content):
                await self._send_notification(user_id, message, message.clean_content, word)
                return
            else:
                for embed in message.embeds:
                    if self._has_word(word, embed.description):
                        await self._send_notification(user_id, message, embed.description, word)
                        return
                    elif self._has_word(word, embed.title):
                        await self._send_notification(user_id, message, embed.title, word)
                        return
                    elif embed.fields is not embed.Empty:
                        for field in embed.fields:
                            if self._has_word(word, field.name):
                                await self._send_notification(user_id, message, field.name, word)
                                return
                            elif self._has_word(word, field.value):
                                await self._send_notification(user_id, message, field.value, word)
                                return

    async def _send_notification(self, user_id: str, message: Message, quote: str, word: str) -> None:
        # Get user to send message to
        user = self.bot.get_user(int(user_id))

        # Escape backticks to avoid breaking output markdown
        quote = quote.replace("`", "'")

        try:
            # Send DM to user without formatting for push notification
            msg = await user.send(f"<{message.author.display_name}> {quote}")

            # Edit DM with nicer formatting
            await msg.edit(content = 
                f".\n**#{message.channel.name}**  {message.channel.guild}```markdown\n"
                f"<{message.author.display_name}> {quote}"
                f"```{message.jump_url}")

            # Log message to console
            log_debug(f"Notify {user.name}#{user.discriminator} on keyword '{word}'")

        except Forbidden as err:
            if err.code == 50007:
                await message.channel.send(f"<@!{user.id}>, I couldn't send you a DM. Please go to 'Privacy Settings' for this server and allow direct messages from server members.")
                log_debug(f"Couldn't DM user {user.name}")


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
            log_debug(f'Adding new user {ctx.author.display_name} to database')
            guilds = [g.id for g in self.bot.guilds if g.get_member(ctx.author.id) is not None]
            self.keywords.add_new_user(guilds, ctx.author.id)

        # Then we'll add the words for this user
        words = [self._clean_mentions(a.lower()) for a in args]
        self.keywords.add_words(ctx.author.id, words)
        words = self.keywords.get_words(ctx.author.id)
        await self._send(ctx, words)

    @notify.group(name='rem', aliases=['remove', 'del', 'delete'])
    async def notify_rem(self, ctx: Context, *args: str) -> None:
        """Remove keywords from list."""
        log_command(ctx)
        words = [self._clean_mentions(a.lower()) for a in args]
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

    @notify.group(name='list', aliases=['all'])
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
            message = 'Keywords: ' + ', '.join(sorted(words))

        try:
            await ctx.author.send(f'```{message}```')
        except Forbidden as err:
            if err.code == 50007:
                await ctx.send(f"<@!{ctx.author.id}>, I couldn't send you a DM. Please go to 'Privacy Settings' for this server and allow direct messages from server members.")
                log_debug(f"Couldn't DM user {ctx.author.name}")
            else:
                log_console(err)


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Keywords(bot))
