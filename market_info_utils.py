# Utility to fetch and cache Upstox market holidays and timings
import requests
import os
import json
from token_utils import load_access_token

def fetch_market_holidays(token=None, out_file="market_holidays.json"):
    token = token or load_access_token()
    if not token:
        raise Exception("Access token required.")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    url = "https://api.upstox.com/v2/market/holidays"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        with open(out_file, "w") as f:
            json.dump(data, f, indent=2)
        return data
    else:
        print(f"Error: {resp.status_code} {resp.text}")
        return None

def fetch_market_timings(token=None, out_file="market_timings.json"):
    token = token or load_access_token()
    if not token:
        raise Exception("Access token required.")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    url = "https://api.upstox.com/v2/market/timings"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        with open(out_file, "w") as f:
            json.dump(data, f, indent=2)
        return data
    else:
        print(f"Error: {resp.status_code} {resp.text}")
        return None

if __name__ == "__main__":
    fetch_market_holidays()
    fetch_market_timings()
