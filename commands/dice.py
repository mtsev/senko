import json
import requests
import random

class Dice:
    def __init__(self, api_key):
        self.api_key = api_key
        self.cache = []
        self.d1k = []
        self.cache_size = 20

    """ Get a number from random.org """
    def random(self, i, j, n):

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
    def roll(self, i, j, n=1):

        # No roll needed if same
        if i == j:
            result = [i for x in range(n)]

        # Generate standard roll, from cache if available
        elif (i == 1 and j == 6):
            if len(self.cache) == 0:
                self.cache += self.random(1, 6, self.cache_size)
            result = self.cache[0:n]
            del self.cache[0]

        # Generate d1k roll, from cache if available
        elif (i == 1 and j == 1000):
            if len(self.d1k) == 0:
                self.d1k += self.random(1, 1000, self.cache_size)
            result = self.d1k[0:n]
            del self.d1k[0]

        # Generate non-standard dice roll
        else:
            result = self.random(i, j, n)

        return result
