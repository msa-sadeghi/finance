import ccxt
config ={
    'exchange': 'binance',
    'symbol': 'BTC/USDT',
    'api_key': 'your_api_key', 
    # جایگزین کنید با API Key خود 'api_secret': 'your_secret', #
    #  جایگزین کنید با Secret خود 'grid_size':100, #
    #  فاصله بین سطوح شبکه (دلار)
    'grid_count':10, 
    # تعداد سطوح در هر جهت 'base_order_size':0.01, #
    #  حجم هر سفارش 'sleep_time':10, #
    #  زمان انتظار بین هرچرخه بررسی سفارشات}
}

def create_exchange():
    exchange_class = getattr(ccxt, config['exchange'])
    exchange = exchange_class({
    'apiKey': config['api_key'],
    'secret': config['api_secret'],
    'enableRateLimit': True,
    })
    return exchange
def fetch_initial_price(exchange, symbol):
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']

def create_grid_levels(initial_price, grid_size, grid_count):
    grid_levels = []
    for i in range(1, grid_count +1):
        buy_price = initial_price - i * grid_size 
        sell_price = initial_price + i * grid_size 
        grid_levels.append({'price': buy_price, 'side': 'buy', 'filled': False})
        grid_levels.append({'price': sell_price, 'side': 'sell', 'filled': False})
    return grid_levels
def place_orders(exchange, symbol, grid_levels, base_order_size):
    orders = []
    for level in grid_levels:
        try:
            order = exchange.create_limit_order(symbol, level['side'], base_order_size, level['price'])
            orders.append(order)
            logging.info(f"Order placed: {level['side']} at {level['price']}")
        except Exception as e:
            logging.error(f"Error placing order: {e}")
    return orders
def main():
    exchange = create_exchange()
    symbol = config['symbol']
    grid_size = config['grid_size']
    grid_count = config['grid_count']
    base_order_size = config['base_order_size']
    sleep_time = config['sleep_time']

    #گرفتن قیمت فعلی initial_price = fetch_initial_price(exchange, symbol)
    logging.info(f"Initial price: {initial_price}")

    # ساخت سطوح شبکه grid_levels = create_grid_levels(initial_price, grid_size, grid_count)

    # قرار دادن سفارشات orders = place_orders(exchange, symbol, grid_levels, base_order_size)

    # حلقه اصلی while True:
    for order in orders[:]:
        try:
            order_status = exchange.fetch_order(order['id'], symbol)
            if order_status['status'] == 'closed':
                logging.info(f"Order filled: {order_status['side']} at {order_status['price']}")
                # قرار دادن سفارش جدید در سطح مجاور if order_status['side'] == 'buy':
                new_price = order_status['price'] + grid_size 
                new_order = exchange.create_limit_order(symbol, 'sell', base_order_size, new_price)
                orders.append(new_order)
                logging.info(f"New sell order placed at {new_price}")
            elif order_status['side'] == 'sell':
                new_price = order_status['price'] - grid_size 
                new_order = exchange.create_limit_order(symbol, 'buy', base_order_size, new_price)
                orders.append(new_order)
                logging.info(f"New buy order placed at {new_price}")
                orders.remove(order)
        except Exception as e:
            logging.error(f"Error processing order {order['id']}: {e}")
            time.sleep(sleep_time)

if __name__ == "__main__":
 main()
