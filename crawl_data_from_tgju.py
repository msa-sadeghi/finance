# نصب کتابخانه
# در ترمینال یا Command Prompt بنویسید:
# pip install tgju-crawl

import tgju_crawl as tg
import pandas as pd
from datetime import datetime, timedelta

def first_approach():
   
    # دریافت قیمت سکه امامی
    print("در حال دریافت داده...")
    data = tg.get_tgju_data(symbol='سکه امامی')
    
    # ببینیم دقیقاً چه ستون‌هایی داریم
    print("\nنام ستون‌های موجود:")
    print(data.columns.tolist())
    
    # نمایش 5 ردیف اول برای دیدن ساختار داده
    print("\n5 روز اول:")
    print(data.head())
    
    # نمایش اطلاعات کلی دیتافریم
    print("\nاطلاعات کلی:")
    print(data.info())
    
    # ذخیره در فایل Excel برای بررسی بیشتر
    data.to_excel('sekeh_100_days.xlsx', index=False)
    print("\nداده‌ها در فایل sekeh_100_days.xlsx ذخیره شد!")
    
    # حالا بر اساس ستون‌های واقعی آمار نمایش بدید
    # فرض می‌کنیم ستون قیمت ممکنه 'p' یا 'price' یا چیز دیگه‌ای باشه
    if 'p' in data.columns:
        print(f"\nبالاترین قیمت: {data['p'].max():,} تومان")
        print(f"پایین‌ترین قیمت: {data['p'].min():,} تومان")
        print(f"میانگین قیمت: {data['p'].mean():,.0f} تومان")
    elif 'price' in data.columns:
        print(f"\nبالاترین قیمت: {data['price'].max():,} تومان")
        print(f"پایین‌ترین قیمت: {data['price'].min():,} تومان")
        print(f"میانگین قیمت: {data['price'].mean():,.0f} تومان")
    else:
        print("\nستون قیمت پیدا نشد. لطفاً فایل Excel رو باز کنید و ببینید.")

