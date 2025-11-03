import numpy as np
import talib

close = np.array([101,103,102,104,106,105,107,110], dtype=float)
sma20 = talib.SMA(close, timeperiod=3)
rsi14 = talib.RSI(close, timeperiod=3)
print(sma20, rsi14)
