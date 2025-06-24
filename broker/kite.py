import os
from kiteconnect import KiteConnect
from config.config import KITE_API_KEY, KITE_API_SECRET

kite = KiteConnect(api_key=KITE_API_KEY)

def kite_login_url():
    return kite.login_url()

# You can add more functions for placing orders, fetching data, etc.
