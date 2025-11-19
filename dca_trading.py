"""
DCA Trading Bot - Dollar Cost Averaging Strategy
نسخه حرفه‌ای و کامل"""
import ccxt
import schedule
import time
import logging
import json
import os
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
import sqlite3

class DCABot:
    def __init__(self, config_path='config.json'):
        """راه‌اندازی اولیه بات"""
        self.config = self.load_config(config_path)
        self.exchange = self.setup_exchange()
        self.bot = Bot(token=self.config['telegram_token'])
        self.chat_id = self.config['telegram_chat_id']
        self.setup_logging()
        self.setup_database()
        
    def load_config(self, config_path):
        """بارگذاری تنظیمات از فایل"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"فایل تنظیمات {config_path} یافت نشد")
            raise
            
    def setup_exchange(self):
        """اتصال به صرافی"""
        exchange_name = self.config.get('exchange', 'binance')
        exchange_class = getattr(ccxt, exchange_name)
        
        return exchange_class({
            'apiKey': self.config['api_key'],
            'secret': self.config['api_secret'],
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
    
    def setup_logging(self):
        """تنظیمات لاگ‌گیری"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('dca_bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_database(self):
        """ایجاد دیتابیس برای ذخیره تاریخچه"""
        conn = sqlite3.connect('dca_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                amount REAL,
                price REAL,
                total_cost REAL,
                status TEXT,
                order_id TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
    def get_current_price(self, symbol):
        """دریافت قیمت فعلی"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            self.logger.error(f"خطا در دریافت قیمت: {e}")
            return None
            
    def save_order_to_db(self, order_data):
        """ذخیره سفارش در دیتابیس"""
        conn = sqlite3.connect('dca_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (timestamp, symbol, amount, price, total_cost, status, order_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_data['timestamp'],
            order_data['symbol'],
            order_data['amount'],
            order_data['price'],
            order_data['total_cost'],
            order_data['status'],
            order_data['order_id']
        ))
        conn.commit()
        conn.close()
        
    def calculate_average_price(self, symbol):
        """محاسبه قیمت میانگین خرید"""
        conn = sqlite3.connect('dca_history.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(amount), SUM(total_cost) 
            FROM orders 
            WHERE symbol = ? AND status = 'completed'
        ''', (symbol,))
        result = cursor.fetchone()
        conn.close()
        
        if result[0] and result[1]:
            total_amount = result[0]
            total_cost = result[1]
            return total_cost / total_amount
        return 0
        
    def send_telegram_message(self, message):
        """ارسال پیام به تلگرام"""
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
        except TelegramError as e:
            self.logger.error(f"خطا در ارسال پیام تلگرام: {e}")
            
    def execute_dca_buy(self):
        """اجرای خرید DCA"""
        symbol = self.config['symbol']
        buy_amount_usd = self.config['buy_amount_usd']
        
        try:
            # دریافت قیمت فعلی
            current_price = self.get_current_price(symbol)
            if not current_price:
                raise Exception("عدم دریافت قیمت")
            
            # محاسبه مقدار خرید
            amount = buy_amount_usd / current_price
            
            # ثبت سفارش
            order = self.exchange.create_market_buy_order(symbol, amount)
            
            # آماده‌سازی داده برای ذخیره
            order_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'amount': amount,
                'price': current_price,
                'total_cost': buy_amount_usd,
                'status': 'completed',
                'order_id': order['id']
            }
            
            # ذخیره در دیتابیس
            self.save_order_to_db(order_data)
            
            # محاسبه قیمت میانگین
            avg_price = self.calculate_average_price(symbol)
            
            # پیام موفقیت
            success_msg = f"""
✅ خرید DCA موفق

نماد: {symbol}
مقدار: {amount:.8f}
قیمت: ${current_price:,.2f}
هزینه کل: ${buy_amount_usd:,.2f}
قیمت میانگین: ${avg_price:,.2f}
زمان: {order_data['timestamp']}
Order ID: {order['id']}
            """
            
            self.logger.info(success_msg)
            self.send_telegram_message(success_msg)
            
        except Exception as e:
            error_msg = f"""
❌ خطا در خرید DCA

نماد: {symbol}
خطا: {str(e)}
زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            self.logger.error(error_msg)
            self.send_telegram_message(error_msg)
            
    def get_portfolio_stats(self):
        """دریافت آمار پورتفولیو"""
        conn = sqlite3.connect('dca_history.db')
        cursor = conn.cursor()
        
        stats = {}
        for symbol in set([self.config['symbol']]):
            cursor.execute('''
                SELECT 
                    COUNT(*), 
                    SUM(amount), 
                    SUM(total_cost),
                    MIN(price),
                    MAX(price)
                FROM orders 
                WHERE symbol = ? AND status = 'completed'
            ''', (symbol,))
            
            result = cursor.fetchone()
            if result[0]:
                stats[symbol] = {
                    'total_purchases': result[0],
                    'total_amount': result[1],
                    'total_invested': result[2],
                    'min_price': result[3],
                    'max_price': result[4],
                    'avg_price': result[2] / result[1] if result[1] else 0
                }
        
        conn.close()
        return stats
        
    def send_daily_report(self):
        """ارسال گزارش روزانه"""
        stats = self.get_portfolio_stats()
        
        report = "📊 گزارش روزانه DCA Bot\n\n"
        
        for symbol, data in stats.items():
            current_price = self.get_current_price(symbol)
            if current_price:
                current_value = data['total_amount'] * current_price
                profit_loss = current_value - data['total_invested']
                profit_loss_pct = (profit_loss / data['total_invested']) * 100
                
                report += f"""
نماد: {symbol}
تعداد خرید: {data['total_purchases']}
مقدار کل: {data['total_amount']:.8f}
سرمایه: ${data['total_invested']:,.2f}
ارزش فعلی: ${current_value:,.2f}
سود/زیان: ${profit_loss:,.2f} ({profit_loss_pct:+.2f}%)
قیمت میانگین: ${data['avg_price']:,.2f}
قیمت فعلی: ${current_price:,.2f}
محدوده قیمت: ${data['min_price']:,.2f} - ${data['max_price']:,.2f}
                """
        
        self.send_telegram_message(report)
        
    def start(self):
        """شروع بات"""
        # زمان‌بندی خرید DCA
        interval = self.config.get('interval', 'weekly')
        buy_time = self.config.get('buy_time', '10:00')
        
        if interval == 'daily':
            schedule.every().day.at(buy_time).do(self.execute_dca_buy)
        elif interval == 'weekly':
            day = self.config.get('buy_day', 'monday')
            getattr(schedule.every(), day).at(buy_time).do(self.execute_dca_buy)
        elif interval == 'monthly':
            # خرید در روز اول هر ماه
            schedule.every().day.at(buy_time).do(self._monthly_check)
            
        # گزارش روزانه
        schedule.every().day.at("20:00").do(self.send_daily_report)
        
        # پیام شروع
        start_msg = f"""
🚀 DCA Bot راه‌اندازی شد

نماد: {self.config['symbol']}
مبلغ خرید: ${self.config['buy_amount_usd']}
بازه: {interval}
زمان خرید: {buy_time}
صرافی: {self.config.get('exchange', 'binance')}
        """
        self.logger.info(start_msg)
        self.send_telegram_message(start_msg)
        
        # حلقه اصلی
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                self.logger.info("بات متوقف شد")
                self.send_telegram_message("⏹ DCA Bot متوقف شد")
                break
            except Exception as e:
                self.logger.error(f"خطای غیرمنتظره: {e}")
                time.sleep(60)
                
    def _monthly_check(self):
        """بررسی برای خرید ماهانه"""
        if datetime.now().day == 1:
            self.execute_dca_buy()


# فایل config.json
"""
{
    "exchange": "binance",
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "telegram_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID",
    "symbol": "BTC/USDT",
    "buy_amount_usd": 100,
    "interval": "weekly",
    "buy_day": "monday",
    "buy_time": "10:00"
}
"""

# اجرای بات
if __name__ == "__main__":
    bot = DCABot('config.json')
    bot.start()
