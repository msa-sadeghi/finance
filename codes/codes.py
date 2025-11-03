import requests
import json

base_url = "https://apiv2.nobitex.ir"
endpoint = "/market/orders/list"
payload = {
    "order": "-price",       # مرتب‌سازی
    "type": "sell",          # نوع سفارش: sell یا buy
    "dstCurrency": "usdt"    # مقصد: usdt / irt / ...
    # در صورت نیاز می‌توانید srcCurrency را نیز اضافه کنید، مثل: "srcCurrency": "btc"
}

resp = requests.post(base_url + endpoint, json=payload, timeout=15)

print("Status:", resp.status_code)
print("Body:", resp.text[:400])  # پیام خطا یا راهنمایی
resp.raise_for_status()
data = resp.json()
print(json.dumps(data, ensure_ascii=False, indent=2))
