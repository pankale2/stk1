import requests
from datetime import datetime

UPSTOX_HOLIDAYS_URL = "https://api.upstox.com/v2/market/holidays"

def is_market_holiday():
    try:
        resp = requests.get(UPSTOX_HOLIDAYS_URL)
        if resp.status_code != 200:
            print(f"[market_holidays] Error fetching holidays: {resp.status_code} {resp.text}")
            return False
        data = resp.json()
        today = datetime.now().strftime('%Y-%m-%d')
        for holiday in data.get('data', []):
            if holiday.get('date') == today:
                return True
        return False
    except Exception as e:
        print(f"[market_holidays] Exception: {e}")
        return False
