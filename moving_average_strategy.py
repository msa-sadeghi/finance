# strategies.py
import pandas as pd
import numpy as np
from indicators import calculate_sma, calculate_ema
class MACrossoverStrategy:
    """
    استراتژی تقاطع میانگین متحرک
    """
    
    def __init__(self, df: pd.DataFrame, 
                 fast_period: int = 20,
                 slow_period: int = 50,
                 ma_type: str = 'SMA'):
        """
        Args:
            df: DataFrame با داده‌های OHLCV
            fast_period: دوره میانگین سریع (پیش‌فرض: 20)
            slow_period: دوره میانگین کند (پیش‌فرض: 50)
            ma_type: نوع میانگین ('SMA' یا 'EMA')
        """
        self.df = df.copy()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type
        
    def calculate_indicators(self):
        """محاسبه میانگین‌های متحرک"""
        if self.ma_type == 'SMA':
            self.df['MA_Fast'] = calculate_sma(self.df, self.fast_period)
            self.df['MA_Slow'] = calculate_sma(self.df, self.slow_period)
        elif self.ma_type == 'EMA':
            self.df['MA_Fast'] = calculate_ema(self.df, self.fast_period)
            self.df['MA_Slow'] = calculate_ema(self.df, self.slow_period)
        else:
            raise ValueError("ma_type باید 'SMA' یا 'EMA' باشد")
        
        print(f"✅ {self.ma_type}({self.fast_period}) و {self.ma_type}({self.slow_period}) محاسبه شدند")
        
    def generate_signals(self):
        """تولید سیگنال‌های خرید و فروش"""
        # شرط خرید: MA سریع از پایین MA کند را قطع کند
        self.df['Signal'] = 0
        
        # 1 = خرید، -1 = فروش
        self.df.loc[self.df['MA_Fast'] > self.df['MA_Slow'], 'Signal'] = 1
        self.df.loc[self.df['MA_Fast'] < self.df['MA_Slow'], 'Signal'] = -1
        
        # تشخیص نقاط تقاطع (جایی که سیگنال تغییر می‌کند)
        self.df['Position'] = self.df['Signal'].diff()
        
        # Position = 2: تقاطع صعودی (Golden Cross) → خرید
        # Position = -2: تقاطع نزولی (Death Cross) → فروش
        
        buy_signals = len(self.df[self.df['Position'] == 2])
        sell_signals = len(self.df[self.df['Position'] == -2])
        
        print(f"✅ تعداد سیگنال‌های خرید: {buy_signals}")
        print(f"✅ تعداد سیگنال‌های فروش: {sell_signals}")
        
    def get_latest_signal(self):
        """دریافت آخرین سیگنال"""
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        print("\n" + "="*60)
        print("📊 وضعیت فعلی")
        print("="*60)
        print(f"قیمت: {last['close']:,.0f}")
        print(f"MA سریع ({self.fast_period}): {last['MA_Fast']:,.0f}")
        print(f"MA کند ({self.slow_period}): {last['MA_Slow']:,.0f}")
        
        if last['Position'] == 2:
            print("\n🟢 سیگنال خرید (Golden Cross)!")
            print("MA سریع از پایین MA کند را قطع کرد")
        elif last['Position'] == -2:
            print("\n🔴 سیگنال فروش (Death Cross)!")
            print("MA سریع از بالا MA کند را قطع کرد")
        elif last['Signal'] == 1:
            print("\n📈 در موقعیت خرید (MA سریع > MA کند)")
        elif last['Signal'] == -1:
            print("\n📉 در موقعیت فروش (MA سریع < MA کند)")
        else:
            print("\n⚪ بدون سیگنال واضح")
            
        return last['Signal']
    
    def backtest(self, initial_capital: float = 10_000_000):
        """
        بک‌تست استراتژی
        
        Args:
            initial_capital: سرمایه اولیه (تومان)
            
        Returns:
            DataFrame با نتایج معاملات
        """
        print("\n" + "="*60)
        print("📈 شروع بک‌تست")
        print("="*60)
        
        capital = initial_capital
        position = 0  # 0 = خارج از بازار، تعداد واحد = در بازار
        entry_price = 0
        trades = []
        
        for i in range(len(self.df)):
            if pd.isna(self.df['Position'].iloc[i]):
                continue
            
            current_price = self.df['close'].iloc[i]
            current_date = self.df.index[i]
            
            # سیگنال خرید (Golden Cross)
            if self.df['Position'].iloc[i] == 2 and position == 0:
                position = capital / current_price
                entry_price = current_price
                print(f"🟢 {current_date}: خرید در {entry_price:,.0f}")
                
            # سیگنال فروش (Death Cross)
            elif self.df['Position'].iloc[i] == -2 and position > 0:
                exit_price = current_price
                profit = (exit_price - entry_price) * position
                capital += profit
                profit_pct = (exit_price - entry_price) / entry_price * 100
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit': profit,
                    'return_pct': profit_pct,
                    'capital': capital
                })
                
                print(f"🔴 {current_date}: فروش در {exit_price:,.0f}")
                print(f"   💰 سود: {profit:,.0f} ({profit_pct:+.2f}%)")
                print(f"   💼 سرمایه: {capital:,.0f}")
                
                position = 0
            
            # ذخیره تاریخ ورود
            if position > 0 and 'entry_date' not in locals():
                entry_date = current_date
        
        # محاسبه آمار کلی
        total_return = (capital - initial_capital) / initial_capital * 100
        
        if trades:
            trades_df = pd.DataFrame(trades)
            winning_trades = len(trades_df[trades_df['profit'] > 0])
            losing_trades = len(trades_df[trades_df['profit'] < 0])
            win_rate = winning_trades / len(trades) * 100
            
            avg_profit = trades_df[trades_df['profit'] > 0]['return_pct'].mean()
            avg_loss = trades_df[trades_df['profit'] < 0]['return_pct'].mean()
        else:
            trades_df = pd.DataFrame()
            winning_trades = losing_trades = 0
            win_rate = avg_profit = avg_loss = 0
        
        # نمایش نتایج
        print("\n" + "="*60)
        print("📊 نتایج بک‌تست")
        print("="*60)
        print(f"سرمایه اولیه: {initial_capital:,.0f}")
        print(f"سرمایه نهایی: {capital:,.0f}")
        print(f"سود/زیان کل: {capital - initial_capital:,.0f}")
        print(f"بازده کل: {total_return:+.2f}%")
        print(f"\nتعداد کل معاملات: {len(trades)}")
        print(f"معاملات سودده: {winning_trades} ({win_rate:.1f}%)")
        print(f"معاملات ضررده: {losing_trades} ({100-win_rate:.1f}%)")
        
        if avg_profit:
            print(f"\nمیانگین سود: +{avg_profit:.2f}%")
        if avg_loss:
            print(f"میانگین ضرر: {avg_loss:.2f}%")
        
        return trades_df
    
    def plot_strategy(self):
        """رسم استراتژی روی نمودار"""
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        
        # نمودار 1: قیمت + میانگین‌ها
        ax1.plot(self.df.index, self.df['close'], label='قیمت', color='black', linewidth=1.5)
        ax1.plot(self.df.index, self.df['MA_Fast'], label=f'MA {self.fast_period}', color='blue')
        ax1.plot(self.df.index, self.df['MA_Slow'], label=f'MA {self.slow_period}', color='red')
        
        # نقاط خرید
        buy_signals = self.df[self.df['Position'] == 2]
        ax1.scatter(buy_signals.index, buy_signals['close'], 
                   color='green', marker='^', s=100, label='خرید', zorder=5)
        
        # نقاط فروش
        sell_signals = self.df[self.df['Position'] == -2]
        ax1.scatter(sell_signals.index, sell_signals['close'], 
                   color='red', marker='v', s=100, label='فروش', zorder=5)
        
        ax1.set_ylabel('قیمت')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title('استراتژی تقاطع میانگین متحرک')
        
        # نمودار 2: سیگنال
        ax2.fill_between(self.df.index, 0, self.df['Signal'], 
                        where=(self.df['Signal']==1), color='green', alpha=0.3, label='خرید')
        ax2.fill_between(self.df.index, 0, self.df['Signal'], 
                        where=(self.df['Signal']==-1), color='red', alpha=0.3, label='فروش')
        ax2.set_ylabel('سیگنال')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('ma_crossover_strategy.png', dpi=300, bbox_inches='tight')
        print("\n📊 نمودار در ma_crossover_strategy.png ذخیره شد")
        plt.show()
