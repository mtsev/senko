class User:
    def __init__(self, id: int, words: list) -> None:
        self.id = id
        self.words = set(words)

    def get_words(self) -> list:
        # Get set of all words
        return list(self.words)

    def add_words(self, words: list) -> None:
        # Add new words to set if not present
        self.words = self.words.union(words)

    def remove_words(self, words: list) -> None:
        # Remove words from set if present
        self.words = self.words.difference(words)


class Guild:
    def __init__(self, id: int) -> None:
        self.id = id
        self.users = {}
        self.usage = 0

    def get_user(self, user_id: int) -> User:
        # Get a user from guild
        return self.users.get(user_id)

    def get_users(self) -> list:
        # Get list of all users from guild
        return self.users.values()

    def add_user(self, user: User) -> None:
        # Add user to guild
        self.users[user.id] = user

    def remove_user(self, user_id: int) -> None:
        # Remove user from guild
        self.users.pop(user_id)


class Cache:
    def __init__(self, capacity: int) -> None:
        self.cache = {}
        self.capacity = capacity

    def keys(self) -> list:
        # Return list of keys (guild IDs) in the cache.
        return self.cache.keys()

    def get_guild(self, guild_id: int) -> list:
        # This is called by Database.get_words() when guild is cached.
        # We want to update usage when cache gets called by Database.get_words()
        # because that means we're checking a new message for keywords.
        self.cache[guild_id].usage += 1

        # Get from cache a list of dicts mapping user_id to set of words.
        # Database doesn't know about User and Guild objects.
        userlist = {}
        for user in self.cache[guild_id].get_users():
            userlist[user.id] = user.get_words()
        return userlist

    def add_guild(self, guild_id: int, data: list) -> None:
        # This is called by Database.get_words() when guild isn't cached.
        # Add a guild to cache, replace LFU if capacity reached.
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

    def has_user(self, user_id: int) -> bool:
        # Check if a user is in cache
        return (self._get_user(user_id) is not None)

    def add_user(self, user_id: int, guild_ids: list, words: list) -> None:
        # Add a new user to cache. This is called when we add a new user to
        # the database or if a user in an uncached guild adds a new word.
        user = User(user_id, words)
        for guild_id in guild_ids:
            if guild_id in self.cache.keys():
                self.cache[guild_id].add_user(user)

    def add_words(self, user_id: int, words: list) -> None:
        # Database should check if user is in cache, but we won't throw errors
        # if it didn't.
        user = self._get_user(user_id)
        if user is not None:
            user.add_words(words)

    def remove_words(self, user_id: int, words: list) -> None:
        # Don't need to do anything if user doesn't exist
        user = self._get_user(user_id)
        if user is not None:
            user.remove_words(words)

    def _get_user(self, user_id: int) -> User:
        for guild in self.cache.values():
            user = guild.get_user(user_id)
            if user is not None:
                return user
