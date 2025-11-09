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

