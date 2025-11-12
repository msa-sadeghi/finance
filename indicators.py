# indicators.py

import pandas as pd

def calculate_sma(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    Calculates the Simple Moving Average (SMA).
    Args:
        df: DataFrame with a 'close' column.
        length: The moving average period.
    Returns:
        A pandas Series with the SMA values.
    """
    return df['close'].rolling(window=length).mean()

def calculate_ema(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    Calculates the Exponential Moving Average (EMA).
    Args:
        df: DataFrame with a 'close' column.
        length: The moving average period.
    Returns:
        A pandas Series with the EMA values.
    """
    return df['close'].ewm(span=length, adjust=False).mean()

def calculate_wma(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    Calculates the Weighted Moving Average (WMA).
    Args:
        df: DataFrame with a 'close' column.
        length: The moving average period.
    Returns:
        A pandas Series with the WMA values.
    """
    weights = pd.Series(range(1, length + 1))
    return df['close'].rolling(window=length).apply(lambda prices: (prices * weights).sum() / weights.sum(), raw=True)

def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI).
    Args:
        df: DataFrame with a 'close' column.
        length: The RSI period.
    Returns:
        A pandas Series with the RSI values.
    """
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=length, min_periods=length).mean()
    avg_loss = loss.rolling(window=length, min_periods=length).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    Calculates the Moving Average Convergence Divergence (MACD).
    Args:
        df: DataFrame with a 'close' column.
        fast: The fast EMA period.
        slow: The slow EMA period.
        signal: The signal line EMA period.
    Returns:
        A DataFrame with MACD, Signal, and Histogram values.
    """
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return pd.DataFrame({'MACD': macd_line, 'Signal': signal_line, 'Histogram': histogram})

def calculate_bollinger_bands(df: pd.DataFrame, length: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """
    Calculates Bollinger Bands.
    Args:
        df: DataFrame with a 'close' column.
        length: The moving average period.
        std_dev: The number of standard deviations.
    Returns:
        A DataFrame with Upper, Middle, and Lower bands.
    """
    middle_band = df['close'].rolling(window=length).mean()
    std = df['close'].rolling(window=length).std()
    
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return pd.DataFrame({'BB_Upper': upper_band, 'BB_Middle': middle_band, 'BB_Lower': lower_band})

def calculate_atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    Calculates the Average True Range (ATR).
    Args:
        df: DataFrame with 'high', 'low', 'close' columns.
        length: The ATR period.
    Returns:
        A pandas Series with ATR values.
    """
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/length, adjust=False).mean()
    return atr

def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """
    Calculates the Stochastic Oscillator.
    Args:
        df: DataFrame with 'high', 'low', 'close' columns.
        k_period: The %K period.
        d_period: The %D (signal line) period.
    Returns:
        A DataFrame with %K and %D values.
    """
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    
    percent_k = 100 * ((df['close'] - low_min) / (high_max - low_min))
    percent_d = percent_k.rolling(window=d_period).mean()
    
    return pd.DataFrame({'%K': percent_k, '%D': percent_d})

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    Calculates the On-Balance Volume (OBV).
    Args:
        df: DataFrame with 'close' and 'volume' columns.
    Returns:
        A pandas Series with OBV values.
    """
    obv = (df['volume'] * (~df['close'].diff().le(0) * 2 - 1)).cumsum()
    return obv

def calculate_cci(df: pd.DataFrame, length: int = 20) -> pd.Series:
    """
    Calculates the Commodity Channel Index (CCI).
    Args:
        df: DataFrame with 'high', 'low', 'close' columns.
        length: The CCI period.
    Returns:
        A pandas Series with CCI values.
    """
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    mean_deviation = typical_price.rolling(window=length).apply(lambda x: (x - x.mean()).abs().mean())
    
    cci = (typical_price - typical_price.rolling(window=length).mean()) / (0.015 * mean_deviation)
    return cci




def calculate_fibonacci_retracement(df: pd.DataFrame, period: int = 100):
    """
    محاسبه سطوح فیبوناچی بر اساس high و low اخیر
    
    Args:
        df: DataFrame با ستون‌های high و low
        period: تعداد کندل‌های اخیر برای یافتن high/low
    
    Returns:
        DataFrame با سطوح فیبوناچی
    """
    # پیدا کردن بالاترین و پایین‌ترین قیمت در period اخیر
    recent_high = df['high'].rolling(window=period).max()
    recent_low = df['low'].rolling(window=period).min()
    
    diff = recent_high - recent_low
    
    # سطوح فیبوناچی کلاسیک
    levels = {
        'Fib_0': recent_high,
        'Fib_236': recent_high - 0.236 * diff,
        'Fib_382': recent_high - 0.382 * diff,
        'Fib_500': recent_high - 0.500 * diff,
        'Fib_618': recent_high - 0.618 * diff,
        'Fib_786': recent_high - 0.786 * diff,
        'Fib_100': recent_low
    }
    
    return pd.DataFrame(levels)


def calculate_ichimoku(df: pd.DataFrame, 
                       tenkan_period: int = 9,
                       kijun_period: int = 26,
                       senkou_span_b_period: int = 52,
                       displacement: int = 26):
    """
    محاسبه ابر ایچیموکو
    
    Returns:
        DataFrame با خطوط Tenkan, Kijun, Senkou A, Senkou B, Chikou
    """
    # Tenkan-sen (خط تبدیل)
    tenkan_sen = (df['high'].rolling(window=tenkan_period).max() + 
                  df['low'].rolling(window=tenkan_period).min()) / 2
    
    # Kijun-sen (خط پایه)
    kijun_sen = (df['high'].rolling(window=kijun_period).max() + 
                 df['low'].rolling(window=kijun_period).min()) / 2
    
    # Senkou Span A (خط پیشرو A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    
    # Senkou Span B (خط پیشرو B)
    senkou_span_b = ((df['high'].rolling(window=senkou_span_b_period).max() + 
                      df['low'].rolling(window=senkou_span_b_period).min()) / 2).shift(displacement)
    
    # Chikou Span (خط تاخیری)
    chikou_span = df['close'].shift(-displacement)
    
    return pd.DataFrame({
        'Tenkan': tenkan_sen,
        'Kijun': kijun_sen,
        'Senkou_A': senkou_span_a,
        'Senkou_B': senkou_span_b,
        'Chikou': chikou_span
    })


def calculate_stochastic_rsi(df: pd.DataFrame, 
                             rsi_period: int = 14,
                             stoch_period: int = 14,
                             k_smooth: int = 3,
                             d_smooth: int = 3):
    """
    محاسبه Stochastic RSI (حساس‌تر از RSI معمولی)
    
    Returns:
        DataFrame با StochRSI_K و StochRSI_D
    """
    # محاسبه RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # محاسبه Stochastic RSI
    rsi_min = rsi.rolling(window=stoch_period).min()
    rsi_max = rsi.rolling(window=stoch_period).max()
    
    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min) * 100
    
    # هموارسازی
    stoch_rsi_k = stoch_rsi.rolling(window=k_smooth).mean()
    stoch_rsi_d = stoch_rsi_k.rolling(window=d_smooth).mean()
    
    return pd.DataFrame({
        'StochRSI_K': stoch_rsi_k,
        'StochRSI_D': stoch_rsi_d
    })


def calculate_volatility_bands(df: pd.DataFrame, 
                               length: int = 20,
                               atr_multiplier: float = 2.0):
    """
    باندهای نوسان بر اساس ATR (جایگزین Bollinger Bands)
    
    Returns:
        DataFrame با Upper, Middle, Lower bands
    """
    from indicators import calculate_atr, calculate_sma
    
    middle = calculate_sma(df, length)
    atr = calculate_atr(df, length)
    
    upper = middle + (atr * atr_multiplier)
    lower = middle - (atr * atr_multiplier)
    
    return pd.DataFrame({
        'Vol_Upper': upper,
        'Vol_Middle': middle,
        'Vol_Lower': lower
    })
