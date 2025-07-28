
import requests
import os
import pandas as pd
import ta
from datetime import datetime, timedelta
from token_utils import load_access_token
from strategy_scrips import SCRIPS

def get_n_working_days_ago(date, n):
    days = 0
    current = date
    while days < n:
        current -= timedelta(days=1)
        if current.weekday() < 5:  # Monday=0, Sunday=6
            days += 1
    return current

def fetch_ohlc(api_client, instrument_token, num_candles=250):
    """
    Fetches the last `num_candles` of 15-min OHLC data for the instrument.
    """
    access_token = os.environ.get('UPSTOX_ACCESS_TOKEN')
    if not access_token and hasattr(api_client, 'configuration'):
        access_token = getattr(api_client.configuration, 'access_token', None)
    if not access_token:
        access_token = load_access_token()
    if not access_token:
        print("No access token available for Upstox historical API call.")
        return None
    # Calculate date range for required candles using working days
    to_dt = datetime.now()
    days_needed = (num_candles // 26) + 5  # Add larger buffer for holidays/weekends
    from_dt = get_n_working_days_ago(to_dt, days_needed)
    from_date = from_dt.strftime('%Y-%m-%d')
    to_date = to_dt.strftime('%Y-%m-%d')
    # Safety: ensure from_date <= to_date
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    interval = 5
    url = f"https://api.upstox.com/v3/historical-candle/{instrument_token}/minutes/{interval}/{to_date}/{from_date}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    try:
        print(f"Requesting: {url}")
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Upstox API error: {resp.status_code} {resp.text}")
            return None
        data = resp.json()
        candles = data.get('data', {}).get('candles', [])
        if not candles:
            print(f"No candle data returned for {instrument_token}")
            return None
        # Each candle: [timestamp, open, high, low, close, volume, open_interest]
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "open_interest"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        # Only keep the last num_candles
        df = df.tail(num_candles)
        print(f"[fetch_ohlc] {instrument_token}: Returned {len(df)} candles. First 5 rows:")
        print(df.head(5))
        print(f"[fetch_ohlc] {instrument_token}: Last 5 rows:")
        print(df.tail(5))
        if not df.empty:
            print(f"[fetch_ohlc] {instrument_token}: Timestamp range: {df.index.min()} to {df.index.max()}")
        return df
    except Exception as e:
        print(f"Error fetching OHLC for {instrument_token}: {e}")
        return None

# Supertrend calculation (ATR 12, multiplier 3)
def add_supertrend(df):
    if len(df) < 15:
        return df
    # True Supertrend calculation (ATR 12, multiplier 3)
    atr_period = 12
    multiplier = 3
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=atr_period, fillna=True).average_true_range()
    df['hl2'] = (df['high'] + df['low']) / 2
    df['upperband'] = df['hl2'] + multiplier * df['atr']
    df['lowerband'] = df['hl2'] - multiplier * df['atr']
    df['in_uptrend'] = True
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        if curr['close'] > prev['upperband']:
            df.at[df.index[i], 'in_uptrend'] = True
        elif curr['close'] < prev['lowerband']:
            df.at[df.index[i], 'in_uptrend'] = False
        else:
            df.at[df.index[i], 'in_uptrend'] = df.at[df.index[i-1], 'in_uptrend']
            if df.at[df.index[i], 'in_uptrend'] and curr['lowerband'] < prev['lowerband']:
                df.at[df.index[i], 'lowerband'] = prev['lowerband']
            if not df.at[df.index[i], 'in_uptrend'] and curr['upperband'] > prev['upperband']:
                df.at[df.index[i], 'upperband'] = prev['upperband']
    df['supertrend'] = df['in_uptrend'].astype(int)
    return df

# DEMA calculation (length 200)
def add_dema(df):
    period = 200
    if len(df) < period:
        df["dema"] = df["close"]
    else:
        # Step 1: First EMA
        ema1 = ta.trend.EMAIndicator(df["close"], window=period, fillna=True).ema_indicator()
        # Step 2: EMA of EMA
        ema2 = ta.trend.EMAIndicator(ema1, window=period, fillna=True).ema_indicator()
        # Step 3: DEMA
        df["dema"] = 2 * ema1 - ema2
    return df

# Entry/exit logic
def check_signal(df):
    if len(df) < 200:
        print("[check_signal] Not enough candles for signal.")
        return None
    last = df.iloc[-1]
    # Placeholder supertrend: 1=positive, 0=negative
    if last["supertrend"] == 1 and last["close"] > last["dema"]:
        print(f"[check_signal] BUY signal triggered: close={last['close']}, dema={last['dema']}, supertrend={last['supertrend']}")
        return "BUY"
    elif last["supertrend"] == 0 and last["close"] < last["dema"]:
        print(f"[check_signal] SELL signal triggered: close={last['close']}, dema={last['dema']}, supertrend={last['supertrend']}")
        return "SELL"
    print(f"[check_signal] No signal: close={last['close']}, dema={last['dema']}, supertrend={last['supertrend']}")
    return None

# Check exit for long/short
# Returns 'EXIT_LONG', 'EXIT_SHORT', or None
def check_exit(df, position):
    if len(df) < 200:
        print("[check_exit] Not enough candles for exit check.")
        return None
    last = df.iloc[-1]
    if position == 'LONG':
        if last['close'] < last['dema'] or last['supertrend'] == 0:
            print(f"[check_exit] EXIT_LONG triggered: close={last['close']}, dema={last['dema']}, supertrend={last['supertrend']}")
            return 'EXIT_LONG'
    elif position == 'SHORT':
        if last['close'] > last['dema'] or last['supertrend'] == 1:
            print(f"[check_exit] EXIT_SHORT triggered: close={last['close']}, dema={last['dema']}, supertrend={last['supertrend']}")
            return 'EXIT_SHORT'
    print(f"[check_exit] No exit: position={position}, close={last['close']}, dema={last['dema']}, supertrend={last['supertrend']}")
    return None

# Calculate P&L for a position
def calc_pnl(position, entry_price, last_price, qty):
    if position == 'LONG':
        return (last_price - entry_price) * qty
    elif position == 'SHORT':
        return (entry_price - last_price) * qty
    return 0
