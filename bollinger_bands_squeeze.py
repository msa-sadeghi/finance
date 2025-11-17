import pandas as pd
import numpy as np
import talib

class BollingerSqueezeStrategy:
    def __init__(self, df, bb_period=20, bb_std=2, squeeze_threshold=0.05, 
                 atr_multiplier=2, risk_per_trade=0.02, commission_rate=0.001, 
                 slippage=0.0005):
        """
        استراتژی Bollinger Bands Squeeze
        
        پارامترها:
        -----------
        bb_period : دوره باندهای بولینگر (پیش‌فرض 20)
        bb_std : ضریب انحراف معیار (پیش‌فرض 2)
        squeeze_threshold : آستانه تشخیص فشردگی (پیش‌فرض 0.05 = 5%)
        """
        self.df = df.copy()
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.squeeze_threshold = squeeze_threshold
        self.atr_multiplier = atr_multiplier
        self.risk_per_trade = risk_per_trade
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self._validate_data()
    
    def _validate_data(self):
        """بررسی صحت داده‌ها"""
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_columns if col not in self.df.columns]
        
        if missing:
            raise ValueError(f"ستون‌های ناموجود: {missing}")
        
        if self.df.isnull().any().any():
            print("⚠️ هشدار: داده‌های ناقص حذف می‌شوند")
            self.df = self.df.dropna()
        
        if len(self.df) < self.bb_period:
            raise ValueError(f"داده کافی نیست. حداقل {self.bb_period} کندل نیاز است")
    
    def calculate_indicators(self):
        """محاسبه Bollinger Bands و اندیکاتورهای کمکی"""
        try:
            # Bollinger Bands با TA-Lib
            self.df['bb_upper'], self.df['bb_middle'], self.df['bb_lower'] = talib.BBANDS(
                self.df['Close'],
                timeperiod=self.bb_period,
                nbdevup=self.bb_std,
                nbdevdn=self.bb_std,
                matype=0
            )
            
            # محاسبه عرض باند (Bandwidth)
            self.df['bandwidth'] = (
                (self.df['bb_upper'] - self.df['bb_lower']) / self.df['bb_middle']
            )
            
            # تشخیص Squeeze (فشردگی)
            self.df['is_squeeze'] = self.df['bandwidth'] < self.squeeze_threshold
            
            # ATR برای Stop Loss
            self.df['atr'] = talib.ATR(
                self.df['High'],
                self.df['Low'],
                self.df['Close'],
                timeperiod=14
            )
            
            # RSI برای فیلتر اضافی
            self.df['rsi'] = talib.RSI(self.df['Close'], timeperiod=14)
            
            # حذف NaN
            self.df = self.df.dropna()
            
            return self.df
            
        except Exception as e:
            raise RuntimeError(f"خطا در محاسبه اندیکاتورها: {e}")
    
    def generate_signals(self):
        """تولید سیگنال‌های خرید/فروش"""
        self.calculate_indicators()
        self.df['signal'] = 0
        self.df['stop_loss'] = np.nan
        self.df['entry_price'] = np.nan
        self.df['trade_type'] = ''
        
        position = 0
        entry_price = 0
        stop_price = 0
        squeeze_ended = False
        
        for i in range(1, len(self.df)):
            row = self.df.iloc[i]
            prev_row = self.df.iloc[i-1]
            
            # بررسی پایان Squeeze
            if prev_row['is_squeeze'] and not row['is_squeeze']:
                squeeze_ended = True
            
            if position == 0:  # بدون پوزیشن
                
                # شرط خرید: پایان Squeeze + شکست باند بالا
                breakout_up = (row['Close'] > row['bb_upper']) and squeeze_ended
                rsi_ok = 30 < row['rsi'] < 70
                
                if breakout_up and rsi_ok:
                    # ورود خرید
                    position = 1
                    entry_price = row['Close'] * (1 + self.slippage)
                    stop_price = entry_price - (self.atr_multiplier * row['atr'])
                    squeeze_ended = False  # ریست کردن
                    
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = 1
                    self.df.iloc[i, self.df.columns.get_loc('stop_loss')] = stop_price
                    self.df.iloc[i, self.df.columns.get_loc('entry_price')] = entry_price
                    self.df.iloc[i, self.df.columns.get_loc('trade_type')] = 'BUY_SQUEEZE'
                
                # شرط فروش: پایان Squeeze + شکست باند پایین
                breakout_down = (row['Close'] < row['bb_lower']) and squeeze_ended
                
                if breakout_down and rsi_ok:
                    # ورود فروش (Short)
                    position = -1
                    entry_price = row['Close'] * (1 - self.slippage)
                    stop_price = entry_price + (self.atr_multiplier * row['atr'])
                    squeeze_ended = False
                    
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = -1
                    self.df.iloc[i, self.df.columns.get_loc('stop_loss')] = stop_price
                    self.df.iloc[i, self.df.columns.get_loc('entry_price')] = entry_price
                    self.df.iloc[i, self.df.columns.get_loc('trade_type')] = 'SELL_SQUEEZE'
            
            elif position == 1:  # در پوزیشن خرید
                # شرط خروج: بازگشت به باند میانی یا حد ضرر
                price_at_middle = row['Close'] <= row['bb_middle']
                stop_loss_hit = row['Close'] <= stop_price
                
                if price_at_middle or stop_loss_hit:
                    position = 0
                    exit_type = 'STOP' if stop_loss_hit else 'MIDDLE'
                    
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = -1
                    self.df.iloc[i, self.df.columns.get_loc('trade_type')] = f'EXIT_{exit_type}'
                else:
                    # Trailing Stop Loss
                    new_stop = row['Close'] - (self.atr_multiplier * row['atr'])
                    if new_stop > stop_price:
                        stop_price = new_stop
                        self.df.iloc[i, self.df.columns.get_loc('stop_loss')] = stop_price
            
            elif position == -1:  # در پوزیشن فروش
                # شرط خروج: بازگشت به باند میانی یا حد ضرر
                price_at_middle = row['Close'] >= row['bb_middle']
                stop_loss_hit = row['Close'] >= stop_price
                
                if price_at_middle or stop_loss_hit:
                    position = 0
                    exit_type = 'STOP' if stop_loss_hit else 'MIDDLE'
                    
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = 1
                    self.df.iloc[i, self.df.columns.get_loc('trade_type')] = f'EXIT_{exit_type}'
        
        self.signals = self.df['signal'].copy()
        return self.signals
    
    def backtest(self, initial_capital=10000):
        """بک‌تست کامل"""
        try:
            self.generate_signals()
            
            # محاسبه position
            self.df['position'] = self.signals.cumsum().clip(-1, 1)
            
            # بازده بازار
            self.df['market_return'] = self.df['Close'].pct_change()
            
            # بازده استراتژی
            self.df['strategy_return'] = self.df['position'].shift(1) * self.df['market_return']
            
            # کسر کارمزد
            self.df['commission'] = abs(self.df['signal']) * self.commission_rate
            self.df['strategy_return'] -= self.df['commission']
            
            # کسر slippage
            self.df.loc[self.df['signal'] != 0, 'strategy_return'] -= self.slippage
            
            # محاسبه position size
            self.df['position_size'] = (
                initial_capital * self.risk_per_trade / 
                (self.atr_multiplier * self.df['atr'])
            )
            
            # نرمالیزاسیون بازده
            self.df['strategy_return'] *= (self.df['position_size'] / initial_capital)
            
            # محاسبه equity
            self.df['equity'] = initial_capital * (1 + self.df['strategy_return']).cumprod()
            
            # معیارهای عملکرد
            results = self._calculate_metrics(initial_capital)
            
            return results
            
        except Exception as e:
            print(f"❌ خطا در بک‌تست: {e}")
            return None
    
    def _calculate_metrics(self, initial_capital):
        """محاسبه معیارهای عملکرد"""
        total_return = (self.df['equity'].iloc[-1] / initial_capital) - 1
        
        sharpe = (
            (self.df['strategy_return'].mean() / self.df['strategy_return'].std()) * np.sqrt(252)
            if self.df['strategy_return'].std() != 0 else 0
        )
        
        max_dd = ((self.df['equity'] / self.df['equity'].cummax()) - 1).min()
        
        win_rate = (
            (self.df['strategy_return'] > 0).sum() / (self.df['strategy_return'] != 0).sum()
            if (self.df['strategy_return'] != 0).sum() > 0 else 0
        )
        
        num_trades = (self.df['signal'] != 0).sum() // 2
        
        winning_trades = self.df[self.df['strategy_return'] > 0]['strategy_return']
        losing_trades = self.df[self.df['strategy_return'] < 0]['strategy_return']
        
        avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(winning_trades.sum() / losing_trades.sum()) if losing_trades.sum() != 0 else 0
        
        # تحلیل نوع خروج
        squeeze_trades = (self.df['trade_type'].str.contains('SQUEEZE', na=False)).sum()
        stop_exits = (self.df['trade_type'].str.contains('STOP', na=False)).sum()
        middle_exits = (self.df['trade_type'].str.contains('MIDDLE', na=False)).sum()
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'num_trades': num_trades,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'final_equity': self.df['equity'].iloc[-1],
            'total_commission': self.df['commission'].sum() * initial_capital,
            'squeeze_trades': squeeze_trades,
            'stop_loss_exits': stop_exits,
            'middle_band_exits': middle_exits
        }
    
    def plot_results(self):
        """نمایش نتایج (نیاز به matplotlib)"""
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)
        
        # نمودار 1: قیمت + باندها
        axes[0].plot(self.df.index, self.df['Close'], label='Close', linewidth=1)
        axes[0].plot(self.df.index, self.df['bb_upper'], 'r--', label='Upper Band', alpha=0.5)
        axes[0].plot(self.df.index, self.df['bb_middle'], 'g--', label='Middle Band', alpha=0.5)
        axes[0].plot(self.df.index, self.df['bb_lower'], 'r--', label='Lower Band', alpha=0.5)
        
        # نمایش سیگنال‌ها
        buy_signals = self.df[self.df['signal'] == 1]
        sell_signals = self.df[self.df['signal'] == -1]
        axes[0].scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', s=100, label='Buy', zorder=5)
        axes[0].scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', s=100, label='Sell', zorder=5)
        
        axes[0].set_ylabel('Price')
        axes[0].legend()
        axes[0].set_title('Bollinger Bands Squeeze Strategy')
        axes[0].grid(True, alpha=0.3)
        
        # نمودار 2: Bandwidth
        axes[1].plot(self.df.index, self.df['bandwidth'], label='Bandwidth', color='blue')
        axes[1].axhline(y=self.squeeze_threshold, color='red', linestyle='--', label='Squeeze Threshold')
        axes[1].fill_between(self.df.index, 0, self.df['bandwidth'], 
                             where=self.df['is_squeeze'], color='red', alpha=0.3, label='Squeeze Zone')
        axes[1].set_ylabel('Bandwidth')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # نمودار 3: Equity
        axes[2].plot(self.df.index, self.df['equity'], label='Strategy Equity', color='green', linewidth=2)
        axes[2].set_ylabel('Equity ($)')
        axes[2].set_xlabel('Date')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


# ─────────────────────────────────────────────
# مثال استفاده
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # فرض کنید df داده‌های قیمت را دارد
    # df = pd.read_csv('btc_data.csv')
    
    # ایجاد استراتژی
    strategy = BollingerSqueezeStrategy(
        df,
        bb_period=20,           # دوره باند
        bb_std=2,               # ضریب انحراف معیار
        squeeze_threshold=0.05, # آستانه فشردگی 5%
        atr_multiplier=2,
        risk_per_trade=0.02,
        commission_rate=0.001,
        slippage=0.0005
    )
    
    # اجرای بک‌تست
    results = strategy.backtest(initial_capital=10000)
    
    # نمایش نتایج
    print("\n" + "="*50)
    print("📊 نتایج Bollinger Bands Squeeze Strategy")
    print("="*50)
    print(f"بازده کل: {results['total_return']*100:.2f}%")
    print(f"نسبت شارپ: {results['sharpe_ratio']:.2f}")
    print(f"حداکثر افت: {results['max_drawdown']*100:.2f}%")
    print(f"نرخ برد: {results['win_rate']*100:.2f}%")
    print(f"تعداد معاملات: {results['num_trades']}")
    print(f"ضریب سود: {results['profit_factor']:.2f}")
    print(f"سرمایه نهایی: ${results['final_equity']:,.2f}")
    print(f"معاملات Squeeze: {results['squeeze_trades']}")
    print(f"خروج با حد ضرر: {results['stop_loss_exits']}")
    print(f"خروج با باند میانی: {results['middle_band_exits']}")
    print("="*50)
    
    # نمایش نمودار
    strategy.plot_results()
