import json
import requests
import random

from discord.ext.commands import *

class RandomAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = []
        self.d1k = []
        self.cache_size = 20

    """ Get a number from random.org """
    def api_request(self, i: int, j: int, n: int) -> list:

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


    """ Return cached result for standard dice, generate otherwise"""
    def roll(self, i: int, j: int, n: int=1) -> list:

        # No roll needed if same
        if i == j:
            result = [i for x in range(n)]

        # Generate standard roll, from cache if available
        elif (i == 1 and j == 6):
            if len(self.cache) == 0:
                self.cache += self.api_request(1, 6, self.cache_size)
            result = self.cache[0:n]
            del self.cache[0]

        # Generate d1k roll, from cache if available
        elif (i == 1 and j == 1000):
            if len(self.d1k) == 0:
                self.d1k += self.api_request(1, 1000, self.cache_size)
            result = self.d1k[0:n]
            del self.d1k[0]

        # Generate non-standard dice roll
        else:
            result = self.api_request(i, j, n)

        return result


class Dice(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.dice = RandomAPI(bot.keys['random'])

    # Initialise dice cache on start up
    @Cog.listener()
    async def on_ready(self):
        self.dice.roll(1, 6)     # initialise dice cache
        self.dice.roll(1, 1000)  # initialise d1k cache

    """ 
    Dice roll command using random.org
    Given no arguments, generates number between 1 and 6 inclusive.
    Given one integer i, generates number between (+-)1 and i inclusive.
    Given two integers i and j, generates number between i and j inclusive.
    Given three integers i, j, and n, generates n numbers between i and j inclusive.
    """
    @command()
    @cooldown(3, 60, BucketType.user)
    async def roll(self, ctx: Context, *args) -> None:
        if ctx.channel.id in self.bot.config['quiet_channels']:
            return

        # More than 3 arguments not handled
        if len(args) > 3:
            return

        # Non-integer arguments not handled
        try:
            args = [int(x) for x in args]
        except ValueError:
            return

        # Roll dice
        async with ctx.typing():
            # No arguments
            if len(args) == 0:
                result = self.dice.roll(1, 6)
            
            # One argument
            elif len(args) == 1:
                if args[0] > 1:
                    result = self.dice.roll(1, args[0])
                elif args[0] < -1:
                    result = self.dice.roll(-1, args[0])
                else:
                    result = [args[0]]

            # Two arguments
            elif len(args) == 2:
                result = self.dice.roll(args[0], args[1])

            # Three arguments
            else:
                result = self.dice.roll(args[0], args[1], args[2])

        # Send number to discord
        message = ', '.join(str(x) for x in result)
        if len(message) > 2000:
            await ctx.send("Your roll is too big for Discord.")
        elif len(message) > 250:
            await ctx.send("Your roll has been sent as a DM.")
            await ctx.author.send(message)
        else:
            await ctx.send(message)


def setup(bot: Bot) -> None:
    bot.add_cog(Dice(bot))
