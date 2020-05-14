#!/usr/bin/env python3
import sys

import pymysql.cursors
import yaml

from cogs.utils.cache import Cache


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
        

# Import config file
with open('config.yaml') as stream:
    config = yaml.safe_load(stream)

# Make database
mydb = Database(config['database'])
print(mydb.get_words(578525886366613504))
