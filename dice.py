import json
import requests
import random

class Dice:
    def __init__(self, api_key):
        self.api_key = api_key
        self.cache = []

    """ Get a number from random.org """
    def roll(self, i, j, n=1):
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

        # Dump results into cache and grab the most recent one
        else:
            self.cache += response["result"]["random"]["data"]
            result = self.cache[-1]
            del self.cache[-1]

        # Don't keep more than 20 numbers in the cache
        del self.cache[:20]

        return result


    """ Return cached result of standard dice roll or generate if none"""
    def cached(self):
        if len(self.cache) > 0:
            result = self.cache[0]
            del self.cache[0]
            return result
        else:
            return roll(1, 6)