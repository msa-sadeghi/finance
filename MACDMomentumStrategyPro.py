import pandas as pd
import numpy as np
import talib

class MACDMomentumStrategyPro:
    """
    استراتژی Momentum با MACD - نسخه حرفه‌ای
    با مدیریت ریسک، کارمزد، و فیلترهای پیشرفته
    """
    
    def __init__(self, df, fast_period=12, slow_period=26, signal_period=9,
                 atr_multiplier=2, risk_per_trade=0.02, 
                 commission_rate=0.001, slippage=0.0005,
                 use_trend_filter=True, trend_ma_period=200):
        """
        Args:
            df: DataFrame با ستون‌های OHLCV
            fast_period: دوره EMA سریع (پیش‌فرض: 12)
            slow_period: دوره EMA کند (پیش‌فرض: 26)
            signal_period: دوره خط سیگنال (پیش‌فرض: 9)
            atr_multiplier: ضریب ATR برای stop loss
            risk_per_trade: درصد ریسک در هر معامله
            commission_rate: نرخ کارمزد (0.001 = 0.1%)
            slippage: لغزش قیمت (0.0005 = 0.05%)
            use_trend_filter: استفاده از فیلتر روند
            trend_ma_period: دوره میانگین برای فیلتر روند
        """
        self.df = df.copy()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.atr_multiplier = atr_multiplier
        self.risk_per_trade = risk_per_trade
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.use_trend_filter = use_trend_filter
        self.trend_ma_period = trend_ma_period
        
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
        
        min_required = max(self.slow_period + self.signal_period, self.trend_ma_period)
        if len(self.df) < min_required:
            raise ValueError(f"داده کافی نیست. حداقل {min_required} کندل نیاز است")
    
    def calculate_indicators(self):
        """محاسبه MACD و سایر اندیکاتورها"""
        try:
            # محاسبه MACD با TA-Lib (سریع‌تر و دقیق‌تر)
            self.df['macd'], self.df['signal'], self.df['histogram'] = talib.MACD(
                self.df['Close'],
                fastperiod=self.fast_period,
                slowperiod=self.slow_period,
                signalperiod=self.signal_period
            )
            
            # ATR برای Stop Loss
            self.df['atr'] = talib.ATR(
                self.df['High'],
                self.df['Low'],
                self.df['Close'],
                timeperiod=14
            )
            
            # فیلتر روند (اختیاری)
            if self.use_trend_filter:
                self.df['trend_ma'] = self.df['Close'].rolling(window=self.trend_ma_period).mean()
                self.df['trend_direction'] = np.where(
                    self.df['Close'] > self.df['trend_ma'], 1, -1
                )
            
            # RSI برای فیلتر اضافی (جلوگیری از ورود در overbought/oversold)
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
        
        for i in range(1, len(self.df)):
            row = self.df.iloc[i]
            prev_row = self.df.iloc[i-1]
            
            if position == 0:  # بدون پوزیشن
                # شرط خرید: تقاطع صعودی MACD
                macd_cross_up = (row['macd'] > row['signal']) and (prev_row['macd'] <= prev_row['signal'])
                
                # فیلترهای اضافی
                histogram_increasing = row['histogram'] > prev_row['histogram']
                trend_ok = (not self.use_trend_filter) or (row['trend_direction'] == 1)
                rsi_ok = (row['rsi'] > 30) and (row['rsi'] < 70)  # نه خیلی oversold نه overbought
                
                if macd_cross_up and histogram_increasing and trend_ok and rsi_ok:
                    # ورود خرید
                    position = 1
                    entry_price = row['Close'] * (1 + self.slippage)
                    stop_price = entry_price - (self.atr_multiplier * row['atr'])
                    
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = 1
                    self.df.iloc[i, self.df.columns.get_loc('stop_loss')] = stop_price
                    self.df.iloc[i, self.df.columns.get_loc('entry_price')] = entry_price
                    self.df.iloc[i, self.df.columns.get_loc('trade_type')] = 'BUY'
            
            elif position == 1:  # در پوزیشن خرید
                # شرط خروج
                macd_cross_down = (row['macd'] < row['signal']) and (prev_row['macd'] >= prev_row['signal'])
                stop_loss_hit = row['Close'] <= stop_price
                
                if macd_cross_down or stop_loss_hit:
                    position = 0
                    exit_type = 'STOP' if stop_loss_hit else 'SIGNAL'
                    
                    self.df.iloc[i, self.df.columns.get_loc('signal')] = -1
                    self.df.iloc[i, self.df.columns.get_loc('trade_type')] = f'SELL_{exit_type}'
                else:
                    # Trailing Stop Loss
                    new_stop = row['Close'] - (self.atr_multiplier * row['atr'])
                    if new_stop > stop_price:
                        stop_price = new_stop
                        self.df.iloc[i, self.df.columns.get_loc('stop_loss')] = stop_price
        
        self.signals = self.df['signal'].copy()
        return self.signals
    
    def backtest(self, initial_capital=10000):
        """بک‌تست کامل با همه جزئیات"""
        try:
            self.generate_signals()
            
            # محاسبه position
            self.df['position'] = self.signals.cumsum().clip(0, 1)
            
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
        stop_exits = (self.df['trade_type'].str.contains('STOP', na=False)).sum()
        signal_exits = (self.df['trade_type'].str.contains('SIGNAL', na=False)).sum()
        
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
            'stop_loss_exits': stop_exits,
            'signal_exits': signal_exits
        }
    
    def print_results(self, results):
        """نمایش نتایج"""
        if results is None:
            print("❌ نتایجی برای نمایش وجود ندارد")
            return
        
        print("\n" + "="*60)
        print("📊 نتایج بک‌تست استراتژی MACD Momentum")
        print("="*60)
        print(f"💰 بازده کل: {results['total_return']:.2%}")
        print(f"📈 نسبت شارپ: {results['sharpe_ratio']:.2f}")
        print(f"📉 حداکثر افت: {results['max_drawdown']:.2%}")
        print(f"🎯 نرخ برد: {results['win_rate']:.2%}")
        print(f"🔄 تعداد معاملات: {results['num_trades']:.0f}")
        print(f"✅ میانگین سود: {results['avg_win']:.4f}")
        print(f"❌ میانگین ضرر: {results['avg_loss']:.4f}")
        print(f"💪 Profit Factor: {results['profit_factor']:.2f}")
        print(f"💵 سرمایه نهایی: ${results['final_equity']:.2f}")
        print(f"💸 کل کارمزد: ${results['total_commission']:.2f}")
        print(f"🛑 خروج با Stop Loss: {results['stop_loss_exits']}")
        print(f"📶 خروج با سیگنال: {results['signal_exits']}")
        print("="*60 + "\n")


# نحوه استفاده:
if __name__ == "__main__":
    # df = pd.read_csv('your_data.csv')
    
    strategy = MACDMomentumStrategyPro(
        df,
        fast_period=12,
        slow_period=26,
        signal_period=9,
        use_trend_filter=True,  # فیلتر روند فعال
        commission_rate=0.001,
        slippage=0.0005
    )
    
    results = strategy.backtest(initial_capital=10000)
    strategy.print_results(results)
