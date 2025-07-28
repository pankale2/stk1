import upstox_client
from upstox_client.rest import ApiException

# Place market order
def place_order(api_client, symbol, side, qty):
    order_api = upstox_client.OrderApi(api_client)
    try:
        order = order_api.place_order(
            api_version="2.0",
            body={
                "quantity": qty,
                "product": "I",  # Intraday
                "validity": "DAY",
                "price": 0,
                "tag": "auto-strategy",
                "instrument_token": symbol,
                "order_type": "MARKET",
                "transaction_type": side,
                "disclosed_quantity": 0,
                "trigger_price": 0.0,
                "is_amo": False,
                "slice": False
            }
        )
        # Upstox v2 returns order_id in order.data.order_id
        return getattr(order, 'data', order)
    except ApiException as e:
        print(f"Order error: {e}")
        return None
