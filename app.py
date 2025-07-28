from flask import Flask, render_template, redirect, url_for, request, session
from broker.upstox import upstox_login_url
import requests
import upstox_client
from upstox_client.rest import ApiException
from datetime import datetime
from scheduler import TradingScheduler
from strategy_scrips import SCRIPS
from strategy import fetch_ohlc, add_supertrend, add_dema, check_signal, check_exit, calc_pnl
from token_utils import load_access_token
from trade_manager import place_order
import threading


app = Flask(__name__)
app.secret_key = "your_secret_key_change_this"  # Change this to a secure secret key


# Scheduler started flag and global access token
_scheduler_started = False
_global_access_token = None

# In-memory state for demo
strategy_state = {
    'signals': {},
    'positions': {},
    'orders': {},
    'last_run': None,
    'current': {},  # symbol: {price, supertrend, dema}
    'history': {},  # symbol: list of dicts (timestamp, ohlc, indicators)
    'order_count': {},  # symbol: today's order count
    'pnl_today': {}     # symbol: today's realized P&L
}

# Strategy logic to be run by scheduler
def run_strategy():
    global _global_access_token
    access_token = _global_access_token or load_access_token()
    if not access_token:
        print("[run_strategy] No access token set globally or in file.")
        return
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_client = upstox_client.ApiClient(configuration)
    now = datetime.now()
    print(f"[run_strategy] Running at {now}, access_token present.")
    for scrip in SCRIPS:
        symbol = scrip['symbol']
        token = scrip['token']
        df = None
        print(f"[run_strategy] Fetching OHLC for {symbol} ({token})...")
        try:
            df = fetch_ohlc(api_client, token, num_candles=250)
            print(f"[run_strategy] Fetched {len(df) if df is not None else 0} rows for {symbol}.")
            if df is not None and hasattr(df, 'head'):
                print(f"[run_strategy] Sample data for {symbol}:\n{df.head()}\n")
        except Exception as e:
            import traceback
            print(f"[run_strategy] Error fetching data for {symbol}: {e}")
            traceback.print_exc()
            strategy_state['current'][symbol] = {'price': '-', 'supertrend': '-', 'dema': '-'}
            strategy_state['history'][symbol] = []
            strategy_state['signals'][symbol] = None
            strategy_state.setdefault('errors', {})[symbol] = str(e)
            continue
        if df is None or len(df) < 1:
            print(f"[run_strategy] No data returned from API for {symbol}.")
            strategy_state['current'][symbol] = {'price': '-', 'supertrend': '-', 'dema': '-'}
            strategy_state['history'][symbol] = []
            strategy_state['signals'][symbol] = None
            strategy_state.setdefault('errors', {})[symbol] = 'No data returned from API.'
            continue
        if len(df) < 200:
            df = add_supertrend(df)
            df = add_dema(df)
            last = df.iloc[-1]
            strategy_state['current'][symbol] = {
                'price': float(last['close']),
                'supertrend': float(last['supertrend']),
                'dema': float(last['dema'])
            }
            candles = []
            for idx, row in df.iloc[-5:].iterrows():
                candles.append({
                    'timestamp': idx.strftime('%Y-%m-%d %H:%M'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'supertrend': float(row['supertrend']),
                    'dema': float(row['dema'])
                })
            strategy_state['history'][symbol] = candles
            strategy_state['signals'][symbol] = None
            continue
        df = add_supertrend(df)
        df = add_dema(df)
        signal = check_signal(df)
        last = df.iloc[-1]
        qty = 1  # Demo: 1 share per trade
        strategy_state['current'][symbol] = {
            'price': float(last['close']),
            'supertrend': float(last['supertrend']),
            'dema': float(last['dema'])
        }
        candles = []
        for idx, row in df.iloc[-5:].iterrows():
            candles.append({
                'timestamp': idx.strftime('%Y-%m-%d %H:%M'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'supertrend': float(row['supertrend']),
                'dema': float(row['dema'])
            })
        strategy_state['history'][symbol] = candles
        # Check for open position
        pos = strategy_state['positions'].get(symbol)
        order_pending = strategy_state['orders'].get(symbol)
        # Entry logic
        if not pos and not order_pending:
            if signal == 'BUY':
                order = place_order(api_client, token, 'BUY', qty)
                if order:
                    order_id = getattr(order, 'order_id', None)
                    if not order_id and hasattr(order, 'data'):
                        order_id = getattr(order.data, 'order_id', None)
                    strategy_state['orders'][symbol] = order_id
                    strategy_state['positions'][symbol] = {'side': 'LONG', 'entry': last['close'], 'qty': qty}
                    strategy_state['order_count'][symbol] = strategy_state['order_count'].get(symbol, 0) + 1
            elif signal == 'SELL':
                order = place_order(api_client, token, 'SELL', qty)
                if order:
                    order_id = getattr(order, 'order_id', None)
                    if not order_id and hasattr(order, 'data'):
                        order_id = getattr(order.data, 'order_id', None)
                    strategy_state['orders'][symbol] = order_id
                    strategy_state['positions'][symbol] = {'side': 'SHORT', 'entry': last['close'], 'qty': qty}
                    strategy_state['order_count'][symbol] = strategy_state['order_count'].get(symbol, 0) + 1
        # Exit logic
        elif pos and not order_pending:
            exit_signal = check_exit(df, pos['side'])
            if (pos['side'] == 'LONG' and exit_signal == 'EXIT_LONG') or (pos['side'] == 'SHORT' and exit_signal == 'EXIT_SHORT'):
                side = 'SELL' if pos['side'] == 'LONG' else 'BUY'
                order = place_order(api_client, token, side, pos['qty'])
                if order:
                    order_id = getattr(order, 'order_id', None)
                    if not order_id and hasattr(order, 'data'):
                        order_id = getattr(order.data, 'order_id', None)
                    strategy_state['orders'][symbol] = order_id
                    # Calculate realized P&L for today
                    entry_price = pos['entry']
                    exit_price = last['close']
                    qty = pos['qty']
                    pnl = calc_pnl(pos['side'], entry_price, exit_price, qty)
                    strategy_state['pnl_today'][symbol] = strategy_state['pnl_today'].get(symbol, 0) + pnl
                    strategy_state['order_count'][symbol] = strategy_state['order_count'].get(symbol, 0) + 1
                    del strategy_state['positions'][symbol]
        strategy_state['signals'][symbol] = signal
    strategy_state['last_run'] = now.strftime('%Y-%m-%d %H:%M:%S')

# Stop-loss checker (every 5 seconds)
def stop_loss_checker():
    global _global_access_token
    access_token = _global_access_token or load_access_token()
    if not access_token:
        return
    configuration = upstox_client.Configuration()
    configuration.access_token = access_token
    api_client = upstox_client.ApiClient(configuration)
    now = datetime.now()
    for scrip in SCRIPS:
        symbol = scrip['symbol']
        token = scrip['token']
        pos = strategy_state['positions'].get(symbol)
        if not pos:
            continue
        from datetime import timedelta
        yesterday = now - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    df = fetch_ohlc(api_client, token, num_candles=250)
    if df is None or len(df) < 1:
        # Skip processing if no data
        return
        last = df.iloc[-1]
        pnl = calc_pnl(pos['side'], pos['entry'], last['close'], pos['qty'])
        if pnl < -100 and not strategy_state['orders'].get(symbol):
            side = 'SELL' if pos['side'] == 'LONG' else 'BUY'
            order = place_order(api_client, token, side, pos['qty'])
            if order:
                strategy_state['orders'][symbol] = order.order_id
                del strategy_state['positions'][symbol]

# Start scheduler after login
def start_scheduler(access_token):
    global _scheduler_started, _global_access_token
    if _scheduler_started:
        return
    _global_access_token = access_token
    sched = TradingScheduler(run_strategy, exit_all)
    t = threading.Thread(target=sched.start)
    t.daemon = True
    t.start()
    # Start stop-loss checker
    def sl_loop():
        import time
        while True:
            stop_loss_checker()
            time.sleep(5)
    sl_thread = threading.Thread(target=sl_loop)
    sl_thread.daemon = True
    sl_thread.start()
    _scheduler_started = True

def exit_all():
    # Exit all open positions at 3:15pm
    strategy_state['positions'] = {}
    strategy_state['orders'] = {}

@app.route('/')
def home():
    if 'access_token' in session:
        return redirect(url_for('holdings'))
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    # Render a login form for Upstox API key and secret
    return render_template('login.html')

@app.route('/login/submit', methods=['POST'])
def login_submit():
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')
    # Store in session for later use
    session['api_key'] = api_key
    session['api_secret'] = api_secret
    # Redirect to Upstox login URL (optionally, pass api_key if needed)
    return redirect(upstox_login_url(api_key))

@app.route('/callback')
def upstox_callback():
    code = request.args.get('code')
    api_key = session.get('api_key')
    api_secret = session.get('api_secret')
    redirect_uri = "http://localhost:5050/callback"  # Must match what you used in upstox_login_url

    # Exchange code for access token
    response = requests.post(
        "https://api.upstox.com/v2/login/authorization/token",
        data={
            "code": code,
            "client_id": api_key,
            "client_secret": api_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
    )
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    if access_token:
        # Store access_token in session
        session['access_token'] = access_token
        start_scheduler(access_token)  # Pass token to scheduler
        return redirect(url_for('dashboard'))
    else:
        return f"Error: {token_data}"

@app.route('/holdings')
def holdings():
    access_token = session.get('access_token') or load_access_token()
    if not access_token:
        return redirect(url_for('login'))
    
    try:
        # Configure API client
        configuration = upstox_client.Configuration()
        configuration.access_token = access_token
        
        # Create API instance
        api_client = upstox_client.ApiClient(configuration)
        portfolio_api = upstox_client.PortfolioApi(api_client)
        
        # Fetch holdings with required api_version parameter
        holdings_response = portfolio_api.get_holdings(api_version='2.0')
        holdings_data = holdings_response.data
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return render_template('holdings.html', holdings=holdings_data, last_updated=now)
        
    except ApiException as e:
        return f"Exception when calling PortfolioApi->get_holdings: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/dashboard')
def dashboard():
    from strategy import SCRIPS
    # Start scheduler if access_token is present and not already started
    if 'access_token' in session:
        start_scheduler(session['access_token'])
    print("[dashboard] Rendering dashboard. strategy_state['last_run']:", strategy_state['last_run'])
    print("[dashboard] strategy_state['current']:", strategy_state['current'])

    # Fetch live positions and orders from Upstox API
    access_token = session.get('access_token') or load_access_token()
    live_positions = {}
    live_orders = {}
    try:
        import upstox_client
        configuration = upstox_client.Configuration()
        configuration.access_token = access_token
        api_client = upstox_client.ApiClient(configuration)
        # Fetch positions
        positions_api = upstox_client.PortfolioApi(api_client)
        positions_resp = positions_api.get_positions(api_version='2.0')  # Fetch positions
        for pos in positions_resp.data:
            symbol = getattr(pos, 'symbol', None)
            if symbol:
                live_positions[symbol] = pos
        # Fetch order history
        orders_api = upstox_client.OrderApi(api_client)
        orders_resp = orders_api.get_order_book(api_version='2.0')
        for order in orders_resp.data:
            symbol = getattr(order, 'symbol', None)
            if symbol:
                if symbol not in live_orders:
                    live_orders[symbol] = []
                live_orders[symbol].append(order)
    except Exception as e:
        print(f"[dashboard] Error fetching live positions/orders: {e}")

    return render_template('dashboard.html', state=strategy_state, SCRIPS=SCRIPS, live_positions=live_positions, live_orders=live_orders)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5050)