import pandas as pd
import numpy as np
import yfinance as yf  # برای داده‌های نمونه (BTC-USD)

class MACrossoverStrategy:
    """
    استراتژی تقاطع Moving Average (Golden/Death Cross)
    """
    
    def __init__(self, df: pd.DataFrame = None, fast_period: int = 20, slow_period: int = 50):
        """
        Args:
            df: DataFrame با ستون 'close' (OHLC)
            fast_period: دوره MA سریع (مثلاً 20)
            slow_period: دوره MA کند (مثلاً 50)
        """
        if df is None:
            # داده نمونه: دانلود BTC از yfinance
            self.df = yf.download('BTC-USD', start='2024-01-01', end='2025-11-15')['Close'].to_frame()
            print("✅ داده‌های نمونه BTC دانلود شد")
        else:
            self.df = df.copy()
            
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    def calculate_indicators(self):
        """محاسبه Moving Average ها"""
        # MA سریع
        self.df['MA_Fast'] = self.df['Close'].rolling(window=self.fast_period).mean()
        
        # MA کند
        self.df['MA_Slow'] = self.df['Close'].rolling(window=self.slow_period).mean()
        
        # حذف ردیف‌های NaN (اولین slow_period ردیف)
        self.df = self.df.dropna()
        
        print(f"✅ MA_Fast({self.fast_period}) و MA_Slow({self.slow_period}) محاسبه شد")
        print(f"📊 تعداد کندل‌های معتبر: {len(self.df)}")
        
    def generate_signals(self):
        """تولید سیگنال‌ها"""
        # Signal: 1=صعودی, -1=نزولی, 0=خنثی
        self.df['Signal'] = 0
        self.df.loc[self.df['MA_Fast'] > self.df['MA_Slow'], 'Signal'] = 1
        self.df.loc[self.df['MA_Fast'] < self.df['MA_Slow'], 'Signal'] = -1
        
        # Position: تشخیص تقاطع (diff Signal)
        self.df['Position'] = self.df['Signal'].diff()
        
        # شمارش تقاطع‌ها
        golden_crosses = len(self.df[self.df['Position'] == 2.0])  # از -1 به 1
        death_crosses = len(self.df[self.df['Position'] == -2.0])  # از 1 به -1
        
        print(f"✅ تعداد Golden Cross (خرید): {golden_crosses}")
        print(f"✅ تعداد Death Cross (فروش): {death_crosses}")
        
        # نمایش DataFrame خلاصه
        print("\n📈 نمونه سیگنال‌ها (5 ردیف آخر):")
        print(self.df[['Close', 'MA_Fast', 'MA_Slow', 'Signal', 'Position']].tail())
        
    def get_latest_signal(self):
        """دریافت آخرین سیگنال"""
        last = self.df.iloc[-1]
        
        print("\n" + "="*60)
        print("📊 وضعیت فعلی MA Crossover")
        print("="*60)
        print(f"قیمت: ${last['Close']:,.2f}")
        print(f"MA سریع ({self.fast_period}): ${last['MA_Fast']:,.2f}")
        print(f"MA کند ({self.slow_period}): ${last['MA_Slow']:,.2f}")
        
        if last['Position'] == 2.0:
            print("\n🟢 سیگنال خرید (Golden Cross)!")
            print("MA سریع از پایین MA کند را قطع کرد")
        elif last['Position'] == -2.0:
            print("\n🔴 سیگنال فروش (Death Cross)!")
            print("MA سریع از بالا MA کند را قطع کرد")
        elif last['Signal'] == 1:
            print("\n📈 در موقعیت خرید (MA سریع > MA کند)")
        elif last['Signal'] == -1:
            print("\n📉 در موقعیت فروش (MA سریع < MA کند)")
        else:
            print("\n⚪ بدون سیگنال واضح (MA ها برابر)")
            
        return last['Signal']  # 1=خرید, -1=فروش, 0=خنثی
        
    def backtest(self, initial_capital: float = 10000):
        """
        بک‌تست استراتژی
        Args:
            initial_capital: سرمایه اولیه (دلار)
        Returns:
            trades_df: DataFrame معاملات
        """
        print("\n" + "="*60)
        print("📈 شروع بک‌تست MA Crossover")
        print("="*60)
        
        capital = initial_capital
        position = 0  # تعداد واحد (0=خارج از بازار)
        entry_price = 0
        entry_date = None
        trades = []
        
        for i in range(len(self.df)):
            current_price = self.df['Close'].iloc[i]
            current_date = self.df.index[i]
            current_position = self.df['Position'].iloc[i]
            
            if pd.isna(current_position):
                continue
                
            # سیگنال خرید (Golden Cross)
            if current_position == 2.0 and position == 0:
                position = capital / current_price  # تمام سرمایه رو بخر
                entry_price = current_price
                entry_date = current_date
                print(f"🟢 {current_date.date()}: خرید در ${entry_price:,.2f} (تعداد: {position:.6f})")
                
            # سیگنال فروش (Death Cross)
            elif current_position == -2.0 and position > 0:
                exit_price = current_price
                profit = (exit_price - entry_price) * position
                capital += profit  # به‌روزرسانی سرمایه
                profit_pct = (exit_price - entry_price) / entry_price * 100
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'position_size': position,
                    'profit': profit,
                    'return_pct': profit_pct,
                    'capital_after': capital
                })
                
                print(f"🔴 {current_date.date()}: فروش در ${exit_price:,.2f}")
                print(f"   💰 سود: ${profit:,.2f} ({profit_pct:+.2f}%)")
                print(f"   💼 سرمایه: ${capital:,.2f}")
                
                position = 0  # خارج از بازار
        
        # اگر هنوز در بازار هستیم، در قیمت آخر بفروش
        if position > 0:
            exit_price = self.df['Close'].iloc[-1]
            profit = (exit_price - entry_price) * position
            capital += profit
            profit_pct = (exit_price - entry_price) / entry_price * 100
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': self.df.index[-1],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'position_size': position,
                'profit': profit,
                'return_pct': profit_pct,
                'capital_after': capital
            })
            
            print(f"🔴 {self.df.index[-1].date()}: فروش نهایی در ${exit_price:,.2f}")
            print(f"   💰 سود نهایی: ${profit:,.2f} ({profit_pct:+.2f}%)")
            print(f"   💼 سرمایه نهایی: ${capital:,.2f}")
        
        # آمار کلی
        total_return = (capital - initial_capital) / initial_capital * 100
        
        if trades:
            trades_df = pd.DataFrame(trades)
            winning_trades = len(trades_df[trades_df['profit'] > 0])
            losing_trades = len(trades_df[trades_df['profit'] < 0])
            win_rate = (winning_trades / len(trades)) * 100 if trades else 0
            
            avg_win = trades_df[trades_df['profit'] > 0]['return_pct'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['profit'] < 0]['return_pct'].mean() if losing_trades > 0 else 0
        else:
            trades_df = pd.DataFrame()
            winning_trades = losing_trades = win_rate = avg_win = avg_loss = 0
        
        # نمایش نتایج
        print("\n" + "="*60)
        print("📊 نتایج بک‌تست")
        print("="*60)
        print(f"سرمایه اولیه: ${initial_capital:,.2f}")
        print(f"سرمایه نهایی: ${capital:,.2f}")
        print(f"سود/زیان کل: ${capital - initial_capital:,.2f}")
        print(f"بازده کل: {total_return:+.2f}%")
        print(f"\nتعداد معاملات: {len(trades)}")
        print(f"معاملات سودده: {winning_trades} ({win_rate:.1f}%)")
        print(f"معاملات ضررده: {losing_trades}")
        if avg_win > 0:
            print(f"میانگین سود: +{avg_win:.2f}%")
        if avg_loss < 0:
            print(f"میانگین ضرر: {avg_loss:.2f}%")
        
        return trades_df  # برای تحلیل بیشتر

# مثال استفاده
if __name__ == "__main__":
    # ایجاد استراتژی
    strategy = MACrossoverStrategy(fast_period=20, slow_period=50)
    
    # محاسبه اندیکاتورها
    strategy.calculate_indicators()
    
    # تولید سیگنال‌ها
    strategy.generate_signals()
    
    # آخرین سیگنال
    latest_signal = strategy.get_latest_signal()
    print(f"\nسیگنال نهایی: {latest_signal}")
    
    # بک‌تست
    results = strategy.backtest(initial_capital=10000)
    print(results)  # نمایش جدول معاملات
