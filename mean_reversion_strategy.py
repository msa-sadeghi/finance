import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # برای visualization (اختیاری)

class MeanReversionStrategy:
    def __init__(self, df, short_window=20, std_dev=2, long_window=200, 
                 slope_threshold=0.005, price_threshold=0.03, atr_multiplier=2, risk_per_trade=0.02):
        """
        پارامترها:
        - df: DataFrame با ستون‌های Close, High, Low
        - short_window: دوره میانگین کوتاه (Bollinger)
        - std_dev: انحراف معیار برای باند
        - long_window: دوره میانگین بلندمدت
        - slope_threshold: آستانه شیب برای فیلتر روند (تغییر روزانه)
        - price_threshold: آستانه فاصله قیمت از میانگین بلندمدت (درصد)
        - atr_multiplier: ضریب ATR برای Stop Loss
        - risk_per_trade: ریسک به ازای هر معامله (درصد از اکوییتی)
        """
        self.df = df.copy()
        self.short_window = short_window
        self.std_dev = std_dev
        self.long_window = long_window
        self.slope_threshold = slope_threshold
        self.price_threshold = price_threshold
        self.atr_multiplier = atr_multiplier
        self.risk_per_trade = risk_per_trade
        self.signals = None
        self.performance = {}
    
    def calculate_indicators(self):
        """محاسبه اندیکاتورها: Bollinger Bands, MA Long, Slope, ATR"""
        # Bollinger Bands
        self.df['ma_short'] = self.df['Close'].rolling(window=self.short_window).mean()
        self.df['std_short'] = self.df['Close'].rolling(window=self.short_window).std()
        self.df['upper_band'] = self.df['ma_short'] + self.std_dev * self.df['std_short']
        self.df['lower_band'] = self.df['ma_short'] - self.std_dev * self.df['std_short']
        
        # میانگین بلندمدت و شیب
        self.df['ma_long'] = self.df['Close'].rolling(window=self.long_window).mean()
        self.df['ma_long_slope'] = self.df['ma_long'].diff()
        
        # ATR برای Stop Loss
        high_low = self.df['High'] - self.df['Low']
        high_close = np.abs(self.df['High'] - self.df['Close'].shift())
        low_close = np.abs(self.df['Low'] - self.df['Close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        self.df['atr'] = true_range.rolling(window=14).mean()
        
        # فیلتر روند: شیب کم + قیمت نزدیک به MA Long
        price_deviation = (self.df['Close'] / self.df['ma_long'] - 1).abs()
        self.df['trend_ok'] = (
            (self.df['ma_long_slope'].abs() < self.slope_threshold) &
            (price_deviation < self.price_threshold)
        )
        
        return self.df  # [web:6][web:21]
    
    def generate_signals(self):
        """تولید سیگنال‌ها با مدیریت پوزیشن و Stop Loss"""
        self.calculate_indicators()
        self.df['signal'] = 0  # 1: Buy, -1: Sell/Exit
        self.df['stop_loss'] = np.nan
        position = 0
        entry_price = 0
        stop_price = 0
        
        for i in range(1, len(self.df)):
            row = self.df.iloc[i]
            
            if position == 0:  # بدون پوزیشن
                if (row['Close'] < row['lower_band']) and row['trend_ok']:
                    # ورود خرید
                    position = 1
                    entry_price = row['Close']
                    stop_price = entry_price - (self.atr_multiplier * row['atr'])
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = 1
                    self.df.iloc[i, self.df.columns.get_loc('stop_loss')] = stop_price
            
            elif position == 1:  # در پوزیشن خرید
                # خروج: بازگشت به میانگین یا Stop Loss
                if (row['Close'] >= row['ma_short']) or (row['Close'] <= stop_price):
                    position = 0
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = -1
                else:
                    # به‌روزرسانی Stop Loss (Trailing optional)
                    new_stop = row['Close'] - (self.atr_multiplier * row['atr'])
                    if new_stop > stop_price:
                        stop_price = new_stop
                        self.df.iloc[i, self.df.columns.get_loc('stop_loss')] = stop_price
        
        self.signals = self.df['signal'].copy()
        return self.signals  # [web:21][web:47]
    
    def backtest(self, initial_capital=100000):
        """بک‌تست با محاسبه بازده، اکوییتی و معیارها"""
        self.generate_signals()
        
        # محاسبه پوزیشن (1 برای Long)
        self.df['position'] = self.signals.cumsum().clip(0, 1)  # فقط Long، max 1 position
        
        # بازده
        self.df['market_return'] = self.df['Close'].pct_change()
        self.df['strategy_return'] = self.df['position'].shift(1) * self.df['market_return']
        
        # اندازه پوزیشن بر اساس ریسک
        self.df['position_size'] = initial_capital * self.risk_per_trade / (self.atr_multiplier * self.df['atr'])
        self.df['strategy_return'] *= (self.df['position_size'] / initial_capital)  # Normalize
        
        # اکوییتی
        self.df['equity'] = initial_capital * (1 + self.df['strategy_return']).cumprod()
        
        # معیارهای عملکرد
        total_return = (self.df['equity'].iloc[-1] / initial_capital) - 1
        sharpe = (self.df['strategy_return'].mean() / self.df['strategy_return'].std()) * np.sqrt(252) if self.df['strategy_return'].std() != 0 else 0
        max_dd = ((self.df['equity'] / self.df['equity'].cummax()) - 1).min()
        win_rate = (self.df['strategy_return'] > 0).sum() / (self.df['strategy_return'] != 0).sum() if (self.df['strategy_return'] != 0).sum() > 0 else 0
        
        self.performance = {
            'Total Return': total_return,
            'Sharpe Ratio': sharpe,
            'Max Drawdown': max_dd,
            'Win Rate': win_rate,
            'Total Trades': (self.signals != 0).sum()
        }
        
        return self.df, self.performance  # [web:21][web:25][web:47]
    
    def plot_results(self):
        """رسم equity curve و سیگنال‌ها (اختیاری)"""
        df_backtest, _ = self.backtest()
        plt.figure(figsize=(12, 6))
        plt.plot(df_backtest.index, df_backtest['equity'], label='Strategy Equity')
        plt.plot(df_backtest.index, df_backtest['Close'] / df_backtest['Close'].iloc[0] * 100000, label='Buy & Hold')
        plt.title('Backtest Results')
        plt.legend()
        plt.show()  # [web:21]

# مثال استفاده
# df = pd.read_csv('btc_data.csv', index_col='Date', parse_dates=True)  # از Nobitex یا CCXT
# df = df.dropna()  # تمیز کردن داده

# strategy = MeanReversionStrategy(df)
# df_backtest, perf = strategy.backtest()
# print(perf)
# strategy.plot_results()
