# import requests
# import time

# def get_btc_price_toman():
#     url = "https://apiv2.nobitex.ir/v3/orderbook/all"
#     try:
#         resp = requests.get(url, timeout=10)
#         if resp.status_code == 200:
#             data = resp.json()
#             price = int(data["BTCIRT"]["lastTradePrice"])
#             print(f"قیمت لحظه‌ای بیت‌کوین به تومان: {price:,}")
#         else:
#             print(f"خطا: {resp.status_code}")
#     except Exception as e:
#         print("خطا در دریافت داده:", e)

# while True:
#     get_btc_price_toman()
#     time.sleep(10)  # به‌روزرسانی هر ۱۰ ثانیه




