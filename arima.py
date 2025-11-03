import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display



# اضافه کردن فونت فارسی (مثلاً Vazir یا Tahoma)
# فونت Tahoma معمولاً روی ویندوز نصب هست
import platform

if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Tahoma'
elif platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'Arial'
else:  # Linux
    # باید فونت فارسی نصب کنید
    plt.rcParams['font.family'] = 'DejaVu Sans'

# از کش matplotlib جلوگیری کنید
plt.rcParams['axes.unicode_minus'] = False


# ========================================
# تابع برای فارسی‌سازی متن
# ========================================

def persian_text(text):
    """
    تبدیل متن فارسی به فرمت قابل نمایش در matplotlib
    
    این تابع دو کار می‌کنه:
    1. حروف رو به هم وصل می‌کنه (reshaping)
    2. جهت متن رو از راست به چپ می‌کنه (bidirectional)
    """
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text






# خواندن داده قیمت سکه
df = pd.read_excel('sekeh_100_days.xlsx')
prices = df['Close']


# ⭐ نرمال‌سازی داده (تقسیم بر 1 میلیون)
prices_normalized = prices / 1_000_000

print("📊 قیمت اصلی - محدوده:")
print(f"   حداقل: {prices.min():,.0f}")
print(f"   حداکثر: {prices.max():,.0f}")

print("\n📊 قیمت نرمال شده - محدوده:")
print(f"   حداقل: {prices_normalized.min():.2f}")
print(f"   حداکثر: {prices_normalized.max():.2f}")
# مدل ARIMA(1, 1, 1)
model = ARIMA(prices_normalized, order=(1, 1, 1))
fitted_model = model.fit()

# نمایش خلاصه
print(fitted_model.summary())

# پیش‌بینی 10 روز آینده
forecast = fitted_model.forecast(steps=10)
print("\nپیش‌بینی 10 روز آینده:")
print(forecast)

# رسم نمودار
plt.figure(figsize=(12, 6))
plt.plot(prices_normalized, label=persian_text('قیمت واقعی'), 
         linewidth=2, 
         alpha=0.7,
         color='#2E86AB')
plt.plot(fitted_model.fittedvalues, label=persian_text('پیش‌بینی مدل'), color='red',linewidth=2, 
         alpha=0.7)
plt.legend()
plt.title(persian_text('ARIMA(1,1,1) - قیمت سکه'),color='red', 
         alpha=0.7)
plt.xlabel(persian_text('روز'),color='red',
         alpha=0.7)
plt.ylabel(persian_text('قیمت (تومان)'),color='red',
         alpha=0.7)
plt.show()

# بررسی خطاها
residuals = fitted_model.resid
plt.figure(figsize=(12, 4))
plt.plot(residuals)
plt.title(persian_text('خطاهای مدل (باید تصادفی باشند)'),color='red', alpha=0.7)
plt.axhline(y=0, color='r', linestyle='--')
plt.show()
