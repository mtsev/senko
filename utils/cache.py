class User:
    def __init__(self, id: int, words: list) -> None:
        self.id = id
        self.words = set(words)

    def get_words(self) -> list:
        """ Get set of all words """
        return list(self.words)

    def add_words(self, words: list) -> int:
        """ Add new words to set if not present. Return size of new list """
        self.words = self.words.union(words)
        return len(self.words)

    def remove_words(self, words: list) -> int:
        """ Remove words from set if present. Return size of new list """
        self.words = self.words.difference(words)
        return len(self.words)


class Guild:
    def __init__(self, id: int) -> None:
        self.id = id
        self.users = {}
        self.usage = 0

    def get_user(self, user_id: int) -> User:
        """ Get a user object from guild """
        return self.users.get(user_id)

    def get_users(self) -> list:
        """ Get list of all users from guild """
        return self.users.values()

    def add_user(self, user: User) -> None:
        """ Add user to guild """
        self.users[user.id] = user

    def remove_user(self, user_id: int) -> None:
        """ Remove user from guild given its ID"""
        self.users.pop(user_id, None)


class Cache:
    def __init__(self, capacity: int) -> None:
        self.cache = {}
        self.capacity = capacity

    def keys(self) -> list:
        """ Return list of keys (guild IDs) in the cache. """
        return self.cache.keys()

    def get_guild(self, guild_id: int) -> dict:
        """ Return dict of users (user IDs) in a guild and their keywords """
        # This is called by Database.get_words() when guild is cached.
        # We want to update usage when cache gets called by Database.get_words()
        # because that means we're checking a new message for keywords.
        self.cache[guild_id].usage += 1

        # Get from cache a dict mapping user_id to set of words.
        # Database doesn't know about User and Guild objects.
        userlist = {}
        for user in self.cache[guild_id].get_users():
            userlist[user.id] = user.get_words()
        return userlist

    def add_guild(self, guild_id: int, data: list) -> None:
        """ Add a guild to cache, replace LFU if capacity reached. """
        # This is called by Database.get_words() when guild isn't cached.
        # Don't worry about capacity for now, we'll handle it later.
        guild = Guild(guild_id)
        user_ids = set([d['user'] for d in data])

        # The same user object is shared between guilds,
        # so we need to check if the user exists first.
        # If not, we make a new user to pass in.
        for user_id in user_ids:
            user = self._get_user(user_id)
            if user is None:
                words = [d['word'] for d in data if d['user'] == user_id]
                user = User(user_id, words)
            guild.add_user(user)  
        self.cache[guild_id] = guild
        print(f"cache.add_guild: {self.get_guild(guild_id)}")

    def remove_guild(self, guild_id: int) -> None:
        """ Remove guild from cache """
        # This gets called if Senko leaves a guild
        self.cache.pop(guild_id, None)

    def add_guild_member(self, guild_id: int, user_id: int) -> None:
        # This gets called if a new member joins a guild that Senko is in.
        # This only gets called if the user is already in cache.
        if guild_id in self.cache.keys():
            user = self._get_user(user_id)
            if user is not None:
                self.cache[guild_id].add_user(user)

    def remove_guild_member(self, guild_id: int, user_id: int) -> None:
        # This gets called if someone leaves a guild that Senko is in.
        # The ex-member may or may not be a user, database doesn't care.
        # Database also doesn't check if guild is in cache or not.
        if guild_id in self.cache.keys():
            self.cache[guild_id].remove_user(user_id)

    def add_user(self, guild_ids: list, user_id: int, words: list) -> None:
        # Add a new user to cache. This is called when we add a new user to
        # the database or when user not in cache joins a cached guild.
        user = User(user_id, words)
        for guild_id in guild_ids:
            if guild_id in self.cache.keys():
                self.cache[guild_id].add_user(user)

    def get_words(self, user_id: int) -> list:
        # Get a user's keyword list
        user = self._get_user(user_id)
        if user is not None:
            return user.get_words()

    def add_words(self, user_id: int, words: list) -> int:
        """ Add words to a cached user's word list.
        Return the number of words user has in cache, or -1 if no such cached user """
        nwords = -1
        user = self._get_user(user_id)
        if user is not None:
            nwords = user.add_words(words)
        return nwords

    def remove_words(self, user_id: int, words: list) -> int:
        """ Remove words from a cached user's word list. 
        Return the number of words user has in cache, or -1 if no such cached user """
        nwords = -1
        user = self._get_user(user_id)
        if user is not None:
            nwords = user.remove_words(words)
        return nwords

    def delete_user(self, user_id: int) -> None:
        """ Remove user from cache """
        user = self._get_user(user_id)
        del user

    def _get_user(self, user_id: int) -> User:
        """ Return a user object from their ID """
        for guild in self.cache.values():
            user = guild.get_user(str(user_id))
            if user is not None:
                return user
            else:
                print(f"User not found for {user_id}")
