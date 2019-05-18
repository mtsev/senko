import json
import requests
import random

class Dice:
    def __init__(self, api_key):
        self.api_key = api_key
        self.cache = []

    """ Get a number from random.org """
    def random(self, i, j, n=1, ret=1):

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
            result = random.randint(min(i, j), max(i, j))

        # If multiple results, dump into cache and grab as needed
        elif n > 1:
            self.cache = response["result"]["random"]["data"] + self.cache
            result = self.cache[0:ret]
            del self.cache[0:ret]

        # Grab the result
        else:
            result = response["result"]["random"]["data"][0]

        return result


    """ Return cached result for standard dice, generate otherwise"""
    def roll(self, i, j):

        # No roll needed if same
        if i == j:
            result = i

        # Generate non-standard dice roll
        elif not (i == 1 and j == 6):
            result = self.random(i, j)

        # Grab standard roll from cache
        elif len(self.cache) > 0:
            result = self.cache[0]
            del self.cache[0]

        # Generate standard roll if empty cache
        else:
            result = self.random(1, 6, 20)

        return result
