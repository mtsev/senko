import json
import requests

class Dice:
    def __init__(self, api_key):
        self.api_key = api_key

    def roll(i,j):
        url = "https://api.random.org/json-rpc/2/invoke"
        headers = {'content-type': 'application/json'}

        # Example echo method
        payload = {
            "jsonrpc": "2.0",
            "method": "generateIntegers",
            "params": {
                "apiKey": self.api_key,
                "n": 1,
                "min": min(i, j),
                "max": max(i, j),
                "replacement": true
            },
            "id": 0,
        }
        
        response = requests.post(url, data=json.dumps(payload), headers=headers).json()
        assert response["id"] == 0
        return response["result"]["random"]["data"][0]
