import pandas as pd
import numpy as np

def ma_crossover(df, fast_period=10, slow_period=50, rsi_period=14, rr_ratio=2.0):
    """
    Enhanced MA crossover with multiple confirmations and adaptive stops
    """
    name = 'Enhanced MA+RSI Crossover'
    
    # Moving averages
    fast = df['close'].ewm(span=fast_period, adjust=False).mean()
    slow = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    # RSI calculation
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = -delta.where(delta < 0, 0).rolling(rsi_period).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    
    # ATR for dynamic stops
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low'] - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    
    # Volume confirmation
    if 'volume' in df.columns:
        volume_sma = df['volume'].rolling(20).mean()
        volume_ratio = df['volume'] / volume_sma
    else:
        volume_ratio = pd.Series([1.0] * len(df), index=df.index)
    
    idx = len(df) - 1
    prev = idx - 1
    
    # Crossover detection
    cross_up = (fast.iloc[prev] <= slow.iloc[prev] and 
                fast.iloc[idx] > slow.iloc[idx])
    cross_dn = (fast.iloc[prev] >= slow.iloc[prev] and 
                fast.iloc[idx] < slow.iloc[idx])
    
    # Enhanced BUY conditions
    if (cross_up and rsi.iloc[idx] > 45 and rsi.iloc[idx] < 75 and
        volume_ratio.iloc[idx] > 1.1 and
        df['close'].iloc[idx] > df['close'].iloc[idx-5]):  # Price momentum
        
        entry = df['close'].iloc[idx]
        sl = entry - atr.iloc[idx] * 2  # ATR-based stop
        risk = entry - sl
        tp = entry + risk * rr_ratio
        confidence = rsi.iloc[idx] - 45 + volume_ratio.iloc[idx] * 10
        
        return {
            'name': name, 'type': 'ma', 'signal': 'buy',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'rsi': rsi.iloc[idx], 'confidence': confidence,
            'volume_ratio': volume_ratio.iloc[idx]
        }
    
    # Enhanced SELL conditions
    if (cross_dn and rsi.iloc[idx] < 55 and rsi.iloc[idx] > 25 and
        volume_ratio.iloc[idx] > 1.1 and
        df['close'].iloc[idx] < df['close'].iloc[idx-5]):  # Price momentum
        
        entry = df['close'].iloc[idx]
        sl = entry + atr.iloc[idx] * 2  # ATR-based stop
        risk = sl - entry
        tp = entry - risk * rr_ratio
        confidence = 55 - rsi.iloc[idx] + volume_ratio.iloc[idx] * 10
        
        return {
            'name': name, 'type': 'ma', 'signal': 'sell',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'rsi': rsi.iloc[idx], 'confidence': confidence,
            'volume_ratio': volume_ratio.iloc[idx]
        }
    
    return None
