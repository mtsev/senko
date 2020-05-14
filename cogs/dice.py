import json
import random

import requests
from discord.ext.commands import Bot, BucketType, Cog, Context, command, cooldown

from .utils.logs import *


class RandomAPI:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.cache = []
        self.d1k = []
        self.cache_size = 20

    def _api_request(self, i: int, j: int, n: int) -> list:
        """ Get a number from random.org """

        # JSON request to random.org API
        url = "https://api.random.org/json-rpc/2/invoke"
        headers = {'content-type': 'application/json'}
        payload = {
            "jsonrpc": "2.0",
            "method": "generateIntegers",
            "params": {
                "apiKey": self.api_key,
                "n": n,
                "min": min(i, j),
                "max": max(i, j),
            },
            "id": 0
        }
        response = requests.post(url, data=json.dumps(payload), headers=headers).json()
        assert response["id"] == 0

        # If something went wrong, generate pseudorandom number
        if "result" not in response:
            result = [random.randint(min(i, j), max(i, j)) for x in range(n)]

        # Grab the result
        else:
            result = response["result"]["random"]["data"]

        return result

    def roll(self, i: int, j: int, n: int=1) -> list:
        """ Return cached result if any, generate otherwise."""

        # No roll needed if same
        if i == j:
            result = [i for x in range(n)]

        # Generate standard roll, from cache if available
        elif (i == 1 and j == 6):
            if len(self.cache) == 0:
                self.cache += self._api_request(1, 6, self.cache_size)
            result = self.cache[0:n]
            del self.cache[0]

        # Generate d1k roll, from cache if available
        elif (i == 1 and j == 1000):
            if len(self.d1k) == 0:
                self.d1k += self._api_request(1, 1000, self.cache_size)
            result = self.d1k[0:n]
            del self.d1k[0]

        # Generate non-standard dice roll
        else:
            result = self._api_request(i, j, n)

        return result


class Dice(Cog):
    """
    Dice roll command using random.org
    Given no arguments, generates number between 1 and 6 inclusive.
    Given one integer j, generates number between 1 and j inclusive.
    Given two integers i and j, generates number between i and j inclusive.
    Given three integers i, j, and n, generates n numbers between i and j inclusive.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.dice = RandomAPI(bot.keys['random'])

    # Initialise dice cache on start up
    @Cog.listener()
    async def on_ready(self) -> None:
        self.dice.roll(1, 6)     # initialise dice cache
        self.dice.roll(1, 1000)  # initialise d1k cache

    @command()
    @cooldown(5, 60, BucketType.user)
    async def roll(self, ctx: Context, j: str='6', i: str='1', n: str='1') -> None:
        if ctx.guild and ctx.guild.id in self.bot.quiet['guilds']:
            return
        if ctx.channel.id in self.bot.quiet['channels']:
            return
        
        log_command(ctx)
        try:
            i = int(i)
            j = int(j)
            n = int(n)
        except ValueError:
            return
        async with ctx.typing():
            result = self.dice.roll(i, j, n)
        await self._send(ctx, result)

    async def _send(self, ctx: Context, result: list) -> None:
        """Send formatted output to Discord."""
        message = ', '.join(str(x) for x in result)
        if len(message) > 2000:
            await ctx.send("Your roll is too big for Discord.")
        elif len(message) > 250:
            await ctx.send("Your roll has been sent as a DM.")
            await ctx.author.send(message)
        else:
            await ctx.send(message)


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Dice(bot))
