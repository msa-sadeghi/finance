import ccxt
import pandas as pd

def fetch_data(symbol='BTC/USDT', timeframe='1h', limit=1000):
    exchange = ccxt.binance()
    # دریافت 1000 کندل آخر
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    # تبدیل به فرمت استاندارد DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# مثال استفاده
df = fetch_data()
print(f"داده دریافت شد: {len(df)} کندل")


import pandas_ta as ta

def add_features(df):
    # 1. اندیکاتورهای تکنیکال
    df['RSI'] = df.ta.rsi(length=14)
    df['EMA_50'] = df.ta.ema(length=50)
    
    # 2. تغییرات قیمت (Returns) - برای نرمال‌سازی
    df['Returns'] = df['close'].pct_change()
    
    # 3. ویژگی‌های تاخیری (Lagged) - مدل باید بداند "دیروز" چه خبر بود
    df['RSI_Lag1'] = df['RSI'].shift(1)
    df['Close_Lag1'] = df['close'].shift(1)
    
    # 4. هدف (Target): آیا کندل "بعدی" مثبت است؟ (1 یا 0)
    # نکته مهم: اینجا از shift(-1) استفاده می‌کنیم (آینده) فقط برای آموزش
    df['Target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    df.dropna(inplace=True) # حذف مقادیر خالی
    return df

df = add_features(df)

from sklearn.ensemble import RandomForestClassifier

# جدا کردن ویژگی‌ها (X) از هدف (y)
features = ['RSI', 'EMA_50', 'Returns', 'RSI_Lag1']
X = df[features]
y = df['Target']

# تقسیم داده‌ها به آموزش (۸۰٪ اول) و تست (۲۰٪ آخر)
train_size = int(len(X) * 0.8)
X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

# ساخت و آموزش مدل
model = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=42)
model.fit(X_train, y_train)
print("مدل آموزش دید.")

from sklearn.metrics import precision_score

# پیش‌بینی روی داده‌های تست
preds = model.predict(X_test)

# محاسبه دقت
precision = precision_score(y_test, preds)
print(f"Dext (Precision): {precision:.2f}") 
# اگر عدد 0.55 باشد یعنی ۵۵٪ سیگنال‌های خرید درست بوده است.
def live_trade():
    # 1. دریافت داده‌های زنده
    live_data = fetch_data(limit=100)
    live_data = add_features(live_data)
    
    # 2. انتخاب آخرین کندل (که هنوز بسته نشده یا تازه بسته شده)
    last_row = live_data.iloc[[-1]][features]
    
    # 3. پرسش از مدل
    prediction = model.predict(last_row)[0]
    
    if prediction == 1:
        print("سیگنال خرید صادر شد! 🚀")
        # exchange.create_market_buy_order(...)
    else:
        print("صبر کنید...")
