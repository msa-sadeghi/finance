import ccxt
import time
import logging
from datetime import datetime

class TriangularArbitrageBot:
    def __init__(self, exchange_id='binance', base_currency='USDT'):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': 'YOUR_API_KEY',
            'secret': 'YOUR_SECRET_KEY',
            'enableRateLimit': True
        })
        self.base_currency = base_currency
        self.min_profit_threshold = 0.5  # حداقل 0.5% سود
        
    def fetch_orderbook(self, symbol):
        """دریافت order book برای محاسبه دقیق قیمت"""
        orderbook = self.exchange.fetch_order_book(symbol)
        bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
        ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
        return {'bid': bid, 'ask': ask}

    def find_triangular_pairs(self):
        """پیدا کردن تمام مثلث‌های ممکن که با USDT شروع می‌شوند"""
        markets = self.exchange.load_markets()
        triangular_pairs = []
        
        # جفت‌هایی که با USDT شروع می‌شوند
        base_pairs = [symbol for symbol in markets if symbol.endswith('/USDT')]
        
        for pair_a in base_pairs:
            coin_a = pair_a.split('/')[0]  # مثلاً BTC
            
            # پیدا کردن جفت‌هایی که coin_a را دارند
            for pair_b in markets:
                if pair_b.startswith(coin_a + '/'):
                    coin_b = pair_b.split('/')[1]  # مثلاً ETH
                    pair_c = f"{coin_b}/USDT"
                    
                    if pair_c in markets:
                        triangular_pairs.append({
                            'path': [pair_a, pair_b, pair_c],
                            'currencies': [self.base_currency, coin_a, coin_b, self.base_currency]
                        })
        
        return triangular_pairs
    
    def calculate_arbitrage_opportunity(self, triangle, starting_amount=1000):
        """محاسبه سود آربیتراژ برای یک مثلث"""
        try:
            pair_a, pair_b, pair_c = triangle['path']
            
            # دریافت قیمت‌های bid/ask
            prices_a = self.fetch_orderbook(pair_a)
            prices_b = self.fetch_orderbook(pair_b)
            prices_c = self.fetch_orderbook(pair_c)
            
            if not all([prices_a['ask'], prices_b['ask'], prices_c['bid']]):
                return None
            
            # مسیر Forward: USDT -> BTC -> ETH -> USDT
            step1 = starting_amount / prices_a['ask']  # خرید BTC
            step2 = step1 / prices_b['ask']  # خرید ETH با BTC
            step3 = step2 * prices_c['bid']  # فروش ETH به USDT
            
            # کسر کارمزد (معمولاً 0.1% در binance)
            fee_rate = 0.001
            final_amount = step3 * (1 - fee_rate) ** 3
            
            profit_loss = final_amount - starting_amount
            profit_percent = (profit_loss / starting_amount) * 100
            
            return {
                'triangle': triangle,
                'profit_percent': profit_percent,
                'profit_amount': profit_loss,
                'final_amount': final_amount,
                'path_type': 'forward'
            }
            
        except Exception as e:
            logging.error(f"Error calculating arbitrage: {e}")
            return None


    def execute_arbitrage(self, opportunity, investment_amount):
        """اجرای معاملات آربیتراژ"""
        try:
            triangle = opportunity['triangle']
            orders = []
            
            # معامله اول: خرید
            order1 = self.exchange.create_market_buy_order(
                triangle['path'][0],
                investment_amount
            )
            orders.append(order1)
            logging.info(f"Order 1 executed: {order1}")
            
            # معامله دوم: خرید
            amount_after_first = order1['filled']
            order2 = self.exchange.create_market_buy_order(
                triangle['path'][1],
                amount_after_first
            )
            orders.append(order2)
            logging.info(f"Order 2 executed: {order2}")
            
            # معامله سوم: فروش و بازگشت به USDT
            amount_after_second = order2['filled']
            order3 = self.exchange.create_market_sell_order(
                triangle['path'][2],
                amount_after_second
            )
            orders.append(order3)
            logging.info(f"Order 3 executed: {order3}")
            
            return orders
            
        except Exception as e:
            logging.error(f"Error executing arbitrage: {e}")
            # پیاده‌سازی استراتژی بازگشت در صورت خطا
            return None
        


    def run(self):
        """حلقه اصلی ربات"""
        logging.info("Bot started. Scanning for opportunities...")
        
        triangles = self.find_triangular_pairs()
        logging.info(f"Found {len(triangles)} triangular pairs")
        
        while True:
            try:
                for triangle in triangles:
                    opportunity = self.calculate_arbitrage_opportunity(triangle)
                    
                    if opportunity and opportunity['profit_percent'] > self.min_profit_threshold:
                        logging.info(f"🎯 Opportunity found! Profit: {opportunity['profit_percent']:.2f}%")
                        
                        # ارسال نوتیفیکیشن تلگرام
                        self.send_telegram_notification(opportunity)
                        
                        # اجرای معامله (در حالت production)
                        # self.execute_arbitrage(opportunity, investment_amount=100)
                        
                time.sleep(1)  # تأخیر 1 ثانیه بین اسکن‌ها
                
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(5)


    import telegram

    def send_telegram_notification(self, opportunity):
        """ارسال پیام به تلگرام"""
        bot = telegram.Bot(token='YOUR_TELEGRAM_BOT_TOKEN')
        message = f"""
        🔔 Arbitrage Opportunity Detected!
        
        Path: {' -> '.join(opportunity['triangle']['currencies'])}
        Profit: {opportunity['profit_percent']:.3f}%
        Amount: ${opportunity['profit_amount']:.2f}
        
        Pairs:
        1️⃣ {opportunity['triangle']['path'][0]}
        2️⃣ {opportunity['triangle']['path'][1]}
        3️⃣ {opportunity['triangle']['path'][2]}
        """
        bot.send_message(chat_id='YOUR_CHAT_ID', text=message)


