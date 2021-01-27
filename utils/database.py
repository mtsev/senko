import pymysql
from discord import Guild

from utils import log
from utils.cache import Cache

class Database:
    def __init__(self, config) -> None:
        self.config = config
        self.cache = Cache(5)
        self.conn = None
        self.init_conn()

    def init_conn(self):
        self.conn = pymysql.connect(
            unix_socket = self.config['socket'],
            user = self.config['user'],
            password = self.config['password'],
            db = self.config['database'],
            charset = 'utf8mb4',
            cursorclass = pymysql.cursors.DictCursor
        )

    def get_guild(self, guild: int) -> dict:
        """ Return dict of users (user IDs) in a guild and their keywords """
        # If guild isn't in cache, update cache
        if guild not in self.cache.keys():
            print("pull from database into cache")
            self.conn.ping(reconnect=True)
            with self.conn.cursor() as cursor:
                query = "CALL get_words (%s)"
                cursor.execute(query, (guild,))
                results = cursor.fetchall()
            self.cache.add_guild(guild, results)

        # Return guild from cache
        temp = self.cache.get_guild(guild)
        print(f"get_guild: {temp}")
        return temp

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
        """ Add words to database """
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
                        log.console(err)
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

        # Check if the users has anymore keywords and remove them if not
        self.remove_user_if_empty(user)

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

    def remove_user_if_empty(self, user: int) -> None:
        """ Check if a user has anymore keywords left and remove them if they don't """
        # This only gets called by remove_words()
        # User may not be cached so check the database
        self.conn.ping(reconnect=True)
        with self.conn.cursor() as cursor:
            query = "SELECT EXISTS (SELECT 1 FROM `keywords` WHERE `user`=%s)"
            cursor.execute(query, (user,))
            result = cursor.fetchone()

        # Remove user from database and cache
        if 0 in result.values():
            with self.conn.cursor() as cursor:
                query = "DELETE FROM `guilds` WHERE `user`=%s"
                cursor.execute(query, (user,))
            self.conn.commit()
            self.cache.delete_user(user)
