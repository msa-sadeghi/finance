# گام 1 و 2: تعریف هدف و جمع‌آوری داده
import pandas as pd
import numpy as np
from pytse_client import Ticker, download
import jdatetime

# تنظیمات اولیه
SYMBOL_1 = 'فولاد'  # سهم اول
SYMBOL_2 = 'ذوب'    # سهم دوم (صنعت مشابه)
TARGET_RETURN = 0.15  # بازده سالانه 15%
SHARPE_MIN = 1.5
MAX_DRAWDOWN = 0.20
HOLDING_DAYS = (5, 30)  # نگهداری 5-30 روز

print("🎯 هدف: استراتژی آربیتراژ آماری با بازده سالانه 15%")
print(f"📊 متریک‌ها: شارپ > {SHARPE_MIN}, Drawdown < {MAX_DRAWDOWN*100}%")

# دانلود داده 5 سال گذشته
print(f"\n📥 در حال دانلود داده {SYMBOL_1} و {SYMBOL_2}...")

ticker1 = Ticker(SYMBOL_1)
ticker2 = Ticker(SYMBOL_2)

# دریافت تاریخچه
df1 = ticker1.history
df2 = ticker2.history

# ذخیره
df1.to_excel(f'{SYMBOL_1}_data.xlsx')
df2.to_excel(f'{SYMBOL_2}_data.xlsx')

print(f"✅ داده {SYMBOL_1}: {len(df1)} روز")
print(f"✅ داده {SYMBOL_2}: {len(df2)} روز")
