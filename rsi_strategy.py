import pandas as pd
class RSIReversalStrategy:
    def __init__(self, df: pd.DataFrame, rsi_period: int = 14,
                 oversold_threshold: int = 30, overbought_threshold: int = 70):
        self.df = df.copy()
        self.rsi_period = rsi_period
        self.oversold = oversold_threshold
        self.overbought = overbought_threshold
        
    def calculate_indicators(self):
        """محاسبه RSI"""
        from indicators import calculate_rsi
        self.df['RSI'] = calculate_rsi(self.df, self.rsi_period)
        print(f"✅ RSI({self.rsi_period}) محاسبه شد")
        
    def generate_signals(self):
        """تولید سیگنال‌ها"""
        self.df['Signal'] = 0
        
        # سیگنال خرید: RSI زیر سطح اشباع فروش
        self.df.loc[self.df['RSI'] < self.oversold, 'Signal'] = 1
        
        # سیگنال فروش: RSI بالای سطح اشباع خرید
        self.df.loc[self.df['RSI'] > self.overbought, 'Signal'] = -1
        
        # تشخیص تغییر (فقط برای نمایش)
        self.df['Position'] = self.df['Signal'].diff()
        
        buy_signals = len(self.df[self.df['Position'] == 2])
        sell_signals = len(self.df[self.df['Position'] == -2])
        
        print(f"✅ تعداد سیگنال‌های خرید: {buy_signals}")
        print(f"✅ تعداد سیگنال‌های فروش: {sell_signals}")
        
    def get_latest_signal(self):
        """دریافت آخرین سیگنال"""
        last = self.df.iloc[-1]
        
        print("\n" + "="*60)
        print("📊 وضعیت فعلی RSI")
        print("="*60)
        print(f"قیمت: {last['close']:,.0f}")
        print(f"RSI({self.rsi_period}): {last['RSI']:.2f}")
        
        if last['Position'] == 2:
            print("\n🟢 سیگنال خرید! (RSI اشباع فروش)")
            print(f"RSI = {last['RSI']:.2f} < {self.oversold}")
        elif last['Position'] == -2:
            print("\n🔴 سیگنال فروش! (RSI اشباع خرید)")
            print(f"RSI = {last['RSI']:.2f} > {self.overbought}")
