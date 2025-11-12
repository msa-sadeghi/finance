import pandas as pd
import numpy as np
from indicators import *
import requests
from datetime import datetime, timedelta
def get_nobitex_ohlc(symbol='BTCIRT', resolution='60', days=7):
    to_time = int(datetime.now().timestamp())
    from_time = int((datetime.now() - timedelta(days=days)).timestamp())
    url = "https://apiv2.nobitex.ir/market/udf/history"
    params = {
        'symbol': symbol,
        'resolution': resolution,
        'from': from_time,
        'to': to_time
    }
    print(f"getting data for {symbol}...")
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        # print(data)
        # print(f"server resp: {data.get('s', 'unknown')}")
        
        if data.get('s') == 'ok':
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(data['t'], unit='s'),
                'open': data['o'],
                'high': data['h'],
                'low': data['l'],
                'close': data['c'],
                'volume': data['v']
            })
            
            df.set_index('timestamp', inplace=True)
            print(f"{len(df)} candle received...")
            return df
        else:
            print(f"error: {data}")
            return None
            
    except Exception as e:
        print(f"error in receiving data: {e}")
        return None
df = get_nobitex_ohlc('BTCIRT', resolution='60', days=7)

if df is not None and len(df) > 50:
    print(df.head())
    print(f"\nshape DataFrame: {df.shape}")
    print(f"columns: {list(df.columns)}")
    
    print("\ncalculate indicators  ...")
    
    df['SMA_20'] = calculate_sma(df, length=20)
    df['RSI'] = calculate_rsi(df, length=14)
    df['CCI'] = calculate_cci(df, length=20)
    
    print("\nindicators calculated")
    last = df.iloc[-1]
    print("\n" + "="*60)
    print("last status BTC/IRT")
    print("="*60)
    print(f"price: {last['close']:,.0f} toman")
    print(f"SMA(20): {last['SMA_20']:,.0f}")
    print(f"RSI(14): {last['RSI']:.2f}")
    print(f"CCI(20): {last['CCI']:.2f}")
    
    # save
    df.to_csv('btc_data.csv')
    print("\n data saved in btc_data.csv ")

else:
    print("\ndata isn't enough")
