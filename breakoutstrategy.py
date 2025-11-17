import pandas as pd
class BreakoutStrategy:
    """
    استراتژی شکست (Breakout)
    """
    
    def __init__(self, df: pd.DataFrame, 
                 period: int = 20,
                 volume_multiplier: float = 1.5):
        """
        Args:
            df: DataFrame با داده‌های OHLCV
            period: تعداد کندل برای یافتن حمایت/مقاومت
            volume_multiplier: حداقل حجم نسبت به میانگین (1.5 = 150% حجم معمولی)
        """
        self.df = df.copy()
        self.period = period
        self.volume_multiplier = volume_multiplier
        
    def calculate_indicators(self):
        """محاسبه سطوح حمایت و مقاومت"""
        # مقاومت = بالاترین قیمت در period اخیر
        self.df['Resistance'] = self.df['high'].rolling(window=self.period).max()
        
        # حمایت = پایین‌ترین قیمت در period اخیر
        self.df['Support'] = self.df['low'].rolling(window=self.period).min()
        
        # میانگین حجم برای تأیید
        self.df['Avg_Volume'] = self.df['volume'].rolling(window=self.period).mean()
        
        print(f"✅ Support/Resistance({self.period}) و Avg_Volume محاسبه شدند")
        
    def generate_signals(self):
        """تولید سیگنال‌های شکست"""
        self.df['Signal'] = 0
        
        # شرط شکست به بالا: قیمت بالای مقاومت + حجم بالای میانگین
        breakout_up = (
            (self.df['close'] > self.df['Resistance']) & 
            (self.df['volume'] > self.df['Avg_Volume'] * self.volume_multiplier)
        )
        self.df.loc[breakout_up, 'Signal'] = 1
        
        # شرط شکست به پایین: قیمت پایین حمایت + حجم بالای میانگین
        breakout_down = (
            (self.df['close'] < self.df['Support']) & 
            (self.df['volume'] > self.df['Avg_Volume'] * self.volume_multiplier)
        )
        self.df.loc[breakout_down, 'Signal'] = -1
        
        # تشخیص تغییر
        self.df['Position'] = self.df['Signal'].diff()
        
        buy_signals = len(self.df[self.df['Position'] == 2])
        sell_signals = len(self.df[self.df['Position'] == -2])
        
        print(f"✅ تعداد شکست‌های صعودی: {buy_signals}")
        print(f"✅ تعداد شکست‌های نزولی: {sell_signals}")
        
    def get_latest_signal(self):
        """دریافت آخرین سیگنال"""
        last = self.df.iloc[-1]
        
        print("\n" + "="*60)
        print("📊 وضعیت فعلی Breakout")
        print("="*60)
        print(f"قیمت: {last['close']:,.0f}")
        print(f"مقاومت: {last['Resistance']:,.0f}")
        print(f"حمایت: {last['Support']:,.0f}")
        print(f"حجم: {last['volume']:,.0f}")
        print(f"حجم میانگین: {last['Avg_Volume']:,.0f}")
        
        if last['Position'] == 2:
            print("\n🟢 شکست صعودی (Breakout Up)!")
            print(f"قیمت {last['close']:,.0f} از مقاومت {last['Resistance']:,.0f} عبور کرد")
            print(f"حجم {last['volume']:,.0f} > {self.volume_multiplier}× میانگین")
        elif last['Position'] == -2:
            print("\n🔴 شکست نزولی (Breakout Down)!")
            print(f"قیمت {last['close']:,.0f} از حمایت {last['Support']:,.0f} عبور کرد")
            print(f"حجم {last['volume']:,.0f} > {self.volume_multiplier}× میانگین")
        elif last['Signal'] == 1:
            print("\n📈 در موقعیت Breakout Up")
        elif last['Signal'] == -1:
            print("\n📉 در موقعیت Breakout Down")
        else:
            print("\n⚪ در محدوده حمایت/مقاومت")
            
        return last['Signal']


