import ccxt
import asyncio
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

class CrossExchangeArbitrageBot:
    def __init__(self, exchanges_config):
        """
        exchanges_config: دیکشنری شامل نام و API keys صرافی‌ها
        مثال: {
            'binance': {'apiKey': '...', 'secret': '...'},
            'kucoin': {'apiKey': '...', 'secret': '...'}
        }
        """
        self.exchanges = {}
        self.initialize_exchanges(exchanges_config)
        self.min_profit_threshold = 1.0  # حداقل 1% سود
        self.max_slippage = 0.2  # حداکثر 0.2% لغزش مجاز
        
    def initialize_exchanges(self, config):
        """راه‌اندازی اتصال به صرافی‌ها"""
        for exchange_id, credentials in config.items():
            try:
                exchange_class = getattr(ccxt, exchange_id)
                self.exchanges[exchange_id] = exchange_class({
                    'apiKey': credentials.get('apiKey'),
                    'secret': credentials.get('secret'),
                    'enableRateLimit': True,  # محدودیت نرخ درخواست
                    'options': {
                        'defaultType': 'spot',  # معاملات اسپات
                    }
                })
                logging.info(f"✅ Connected to {exchange_id}")
            except Exception as e:
                logging.error(f"❌ Error connecting to {exchange_id}: {e}")


    async def fetch_ticker_async(self, exchange_id, symbol):
        """دریافت قیمت از یک صرافی به صورت async"""
        try:
            exchange = self.exchanges[exchange_id]
            ticker = await exchange.fetch_ticker_async(symbol)
            return {
                'exchange': exchange_id,
                'symbol': symbol,
                'bid': ticker['bid'],  # بهترین قیمت خرید
                'ask': ticker['ask'],  # بهترین قیمت فروش
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            logging.error(f"Error fetching {symbol} from {exchange_id}: {e}")
            return None

    async def fetch_all_prices(self, symbol):
        """دریافت قیمت از همه صرافی‌ها به صورت همزمان"""
        tasks = []
        for exchange_id in self.exchanges.keys():
            task = self.fetch_ticker_async(exchange_id, symbol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # فیلتر کردن نتایج معتبر
        valid_results = [r for r in results if r and not isinstance(r, Exception)]
        return valid_results
    

    def calculate_arbitrage_profit(self, prices, investment_amount=1000):
        """
        محاسبه سود آربیتراژ برای تمام ترکیبات ممکن صرافی‌ها
        """
        opportunities = []
        
        for i, buy_exchange in enumerate(prices):
            for j, sell_exchange in enumerate(prices):
                if i >= j:  # جلوگیری از تکرار
                    continue
                    
                # قیمت خرید از صرافی اول (ask price)
                buy_price = buy_exchange['ask']
                # قیمت فروش در صرافی دوم (bid price)
                sell_price = sell_exchange['bid']
                
                if not buy_price or not sell_price:
                    continue
                
                # محاسبه مقدار ارز که می‌توان خرید
                buy_fee = self.get_trading_fee(buy_exchange['exchange'])
                sell_fee = self.get_trading_fee(sell_exchange['exchange'])
                withdrawal_fee = self.get_withdrawal_fee(
                    buy_exchange['exchange'], 
                    buy_exchange['symbol']
                )
                
                # مقدار ارز بعد از خرید
                amount_bought = (investment_amount / buy_price) * (1 - buy_fee)
                
                # مقدار بعد از انتقال
                amount_after_withdrawal = amount_bought - withdrawal_fee
                
                # مقدار دلار بعد از فروش
                amount_after_sell = (amount_after_withdrawal * sell_price) * (1 - sell_fee)
                
                # محاسبه سود
                profit = amount_after_sell - investment_amount
                profit_percent = (profit / investment_amount) * 100
                
                # زمان انتقال تقریبی
                transfer_time = self.estimate_transfer_time(
                    buy_exchange['exchange'],
                    sell_exchange['exchange']
                )
                
                if profit_percent > self.min_profit_threshold:
                    opportunities.append({
                        'buy_exchange': buy_exchange['exchange'],
                        'sell_exchange': sell_exchange['exchange'],
                        'symbol': buy_exchange['symbol'],
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_amount': profit,
                        'profit_percent': profit_percent,
                        'investment': investment_amount,
                        'final_amount': amount_after_sell,
                        'transfer_time': transfer_time,
                        'timestamp': datetime.now()
                    })
        
        return sorted(opportunities, key=lambda x: x['profit_percent'], reverse=True)

    def get_trading_fee(self, exchange_id):
        """دریافت کارمزد معاملات"""
        fee_structure = {
            'binance': 0.001,   # 0.1%
            'kucoin': 0.001,    # 0.1%
            'okx': 0.0008,      # 0.08%
            'bybit': 0.001,     # 0.1%
            'gate': 0.002,      # 0.2%
        }
        return fee_structure.get(exchange_id, 0.002)

    def get_withdrawal_fee(self, exchange_id, symbol):
        """دریافت کارمزد برداشت"""
        # این مقادیر باید از API صرافی دریافت شوند
        base_currency = symbol.split('/')[0]
        
        withdrawal_fees = {
            'binance': {'BTC': 0.0005, 'ETH': 0.005, 'USDT': 1},
            'kucoin': {'BTC': 0.0005, 'ETH': 0.01, 'USDT': 1},
            'okx': {'BTC': 0.0004, 'ETH': 0.006, 'USDT': 0.8},
        }
        
        return withdrawal_fees.get(exchange_id, {}).get(base_currency, 0)

    def estimate_transfer_time(self, from_exchange, to_exchange):
        """تخمین زمان انتقال بین صرافی‌ها (به دقیقه)"""
        transfer_times = {
            ('binance', 'kucoin'): 15,
            ('binance', 'okx'): 10,
            ('kucoin', 'okx'): 20,
        }
        
        key = (from_exchange, to_exchange)
        return transfer_times.get(key, 30)  # پیش‌فرض 30 دقیقه
    


    async def execute_arbitrage(self, opportunity):
        """
        اجرای کامل یک فرصت آربیتراژ
        """
        try:
            buy_exchange_id = opportunity['buy_exchange']
            sell_exchange_id = opportunity['sell_exchange']
            symbol = opportunity['symbol']
            investment = opportunity['investment']
            
            # مرحله 1: بررسی موجودی
            balance_check = await self.check_balances(
                buy_exchange_id, 
                sell_exchange_id, 
                symbol,
                investment
            )
            
            if not balance_check['sufficient']:
                logging.warning(f"❌ Insufficient balance for arbitrage")
                return None
            
            # مرحله 2: خرید از صرافی اول
            buy_order = await self.place_market_order(
                buy_exchange_id,
                symbol,
                'buy',
                investment
            )
            
            if not buy_order or buy_order['status'] != 'closed':
                logging.error(f"❌ Buy order failed on {buy_exchange_id}")
                return None
            
            logging.info(f"✅ Bought {buy_order['filled']} {symbol} on {buy_exchange_id}")
            
            # مرحله 3: انتقال به صرافی دوم
            withdrawal = await self.withdraw_crypto(
                buy_exchange_id,
                sell_exchange_id,
                symbol,
                buy_order['filled']
            )
            
            if not withdrawal:
                logging.error(f"❌ Withdrawal failed")
                # استراتژی بازگشت: فروش در همان صرافی
                await self.place_market_order(buy_exchange_id, symbol, 'sell', buy_order['filled'])
                return None
            
            # مرحله 4: منتظر تایید انتقال
            await self.wait_for_deposit(sell_exchange_id, symbol, buy_order['filled'])
            
            # مرحله 5: فروش در صرافی دوم
            sell_order = await self.place_market_order(
                sell_exchange_id,
                symbol,
                'sell',
                buy_order['filled']
            )
            
            if sell_order and sell_order['status'] == 'closed':
                actual_profit = sell_order['cost'] - investment
                logging.info(f"🎉 Arbitrage completed! Profit: ${actual_profit:.2f}")
                
                return {
                    'success': True,
                    'buy_order': buy_order,
                    'sell_order': sell_order,
                    'actual_profit': actual_profit,
                    'expected_profit': opportunity['profit_amount']
                }
            else:
                logging.error(f"❌ Sell order failed on {sell_exchange_id}")
                return None
            
        except Exception as e:
            logging.error(f"❌ Error executing arbitrage: {e}")
            return None

    async def place_market_order(self, exchange_id, symbol, side, amount):
        """ثبت سفارش مارکت"""
        try:
            exchange = self.exchanges[exchange_id]
            
            if side == 'buy':
                # برای خرید، مقدار به USDT است
                order = await exchange.create_market_buy_order_async(symbol, None, {'quoteOrderQty': amount})
            else:
                # برای فروش، مقدار به coin است
                order = await exchange.create_market_sell_order_async(symbol, amount)
            
            logging.info(f"Order placed: {side} {amount} {symbol} on {exchange_id}")
            return order
            
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return None

    async def withdraw_crypto(self, from_exchange_id, to_exchange_id, symbol, amount):
        """انتقال ارز بین صرافی‌ها"""
        try:
            # دریافت آدرس واریز صرافی مقصد
            to_exchange = self.exchanges[to_exchange_id]
            deposit_address = await to_exchange.fetch_deposit_address_async(symbol.split('/')[0])
            
            # انجام برداشت از صرافی مبدا
            from_exchange = self.exchanges[from_exchange_id]
            withdrawal = await from_exchange.withdraw_async(
                symbol.split('/')[0],
                amount,
                deposit_address['address'],
                tag=deposit_address.get('tag'),
                params={}
            )
            
            logging.info(f"Withdrawal initiated: {withdrawal['id']}")
            return withdrawal
            
        except Exception as e:
            logging.error(f"Withdrawal error: {e}")
            return None

    async def wait_for_deposit(self, exchange_id, symbol, expected_amount, timeout=3600):
        """منتظر واریز در صرافی مقصد"""
        start_time = time.time()
        base_currency = symbol.split('/')[0]
        
        while time.time() - start_time < timeout:
            try:
                deposits = await self.exchanges[exchange_id].fetch_deposits_async(base_currency)
                
                # بررسی آخرین واریزها
                for deposit in deposits[:5]:
                    if deposit['amount'] >= expected_amount * 0.99:  # با 1% تلرانس
                        if deposit['status'] == 'ok':
                            logging.info(f"✅ Deposit confirmed on {exchange_id}")
                            return True
                
                await asyncio.sleep(30)  # هر 30 ثانیه چک کن
                
            except Exception as e:
                logging.error(f"Error checking deposits: {e}")
                await asyncio.sleep(60)
        
        logging.error(f"❌ Deposit timeout after {timeout} seconds")
        return False


    async def run_monitoring(self, symbols, auto_execute=False):
        """
        حلقه اصلی مانیتورینگ
        symbols: لیست جفت ارزها مثل ['BTC/USDT', 'ETH/USDT']
        auto_execute: اجرای خودکار یا فقط نمایش
        """
        logging.info(f"🚀 Bot started. Monitoring {len(symbols)} pairs across {len(self.exchanges)} exchanges")
        
        while True:
            try:
                for symbol in symbols:
                    # دریافت قیمت‌ها از همه صرافی‌ها
                    prices = await self.fetch_all_prices(symbol)
                    
                    if len(prices) < 2:
                        continue
                    
                    # محاسبه فرصت‌های آربیتراژ
                    opportunities = self.calculate_arbitrage_profit(prices, investment_amount=1000)
                    
                    # نمایش بهترین فرصت
                    if opportunities:
                        best = opportunities[0]
                        logging.info(f"""
                        🎯 Arbitrage Opportunity Found!
                        Symbol: {best['symbol']}
                        Buy: {best['buy_exchange']} @ ${best['buy_price']:.2f}
                        Sell: {best['sell_exchange']} @ ${best['sell_price']:.2f}
                        Profit: {best['profit_percent']:.2f}% (${best['profit_amount']:.2f})
                        Transfer Time: ~{best['transfer_time']} min
                        """)
                        
                        # ارسال نوتیفیکیشن
                        await self.send_notification(best)
                        
                        # اجرای خودکار در صورت فعال بودن
                        if auto_execute and best['profit_percent'] > 2.0:  # فقط برای سود بالای 2%
                            result = await self.execute_arbitrage(best)
                            
                            if result and result['success']:
                                logging.info(f"✅ Auto-trade executed successfully!")
                    
                # تأخیر بین اسکن‌ها (برای جلوگیری از rate limit)
                await asyncio.sleep(5)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)


    async def check_balances(self, buy_exchange_id, sell_exchange_id, symbol, amount):
        """بررسی موجودی در هر دو صرافی"""
        try:
            buy_exchange = self.exchanges[buy_exchange_id]
            sell_exchange = self.exchanges[sell_exchange_id]
            
            buy_balance = await buy_exchange.fetch_balance_async()
            sell_balance = await sell_exchange.fetch_balance_async()
            
            quote_currency = symbol.split('/')[1]  # معمولاً USDT
            base_currency = symbol.split('/')[0]   # مثلاً BTC
            
            # بررسی موجودی برای خرید
            available_for_buy = buy_balance['free'].get(quote_currency, 0)
            
            # بررسی اینکه آیا در صرافی فروش جای واریز هست
            available_for_sell = sell_balance['free'].get(base_currency, 0)
            
            sufficient = available_for_buy >= amount
            
            return {
                'sufficient': sufficient,
                'buy_balance': available_for_buy,
                'sell_balance': available_for_sell
            }
            
        except Exception as e:
            logging.error(f"Error checking balances: {e}")
            return {'sufficient': False}

    async def rebalance_funds(self):
        """توازن مجدد موجودی بین صرافی‌ها"""
        # این تابع موجودی USDT را بین صرافی‌ها متعادل می‌کند
        # تا همیشه آماده برای فرصت‌های آربیتراژ باشید
        pass



