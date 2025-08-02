import pandas as pd
import numpy as np

def fibonacci_system(df, lookback=100, rr_ratio=2.0, proximity_threshold=0.01):
    """
    Enhanced Fibonacci retracement with momentum confirmation
    """
    name = 'Enhanced Fibonacci'
    idx = len(df) - 1
    
    # Find swing high and low
    high = df['high'].rolling(lookback).max().iloc[-1]
    low = df['low'].rolling(lookback).min().iloc[-1]
    entry = df['close'].iloc[-1]
    
    # RSI for momentum confirmation
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss)).iloc[-1]
    
    # MACD for trend confirmation
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9).mean()
    macd_histogram = macd - macd_signal
    
    levels = [0.236, 0.382, 0.5, 0.618, 0.786]
    fibs = [(high - (high - low) * lvl) for lvl in levels]
    
    # Find closest Fibonacci level
    diffs = [abs(entry - lvl) / entry for lvl in fibs]
    min_diff_idx = diffs.index(min(diffs))
    closest_fib = fibs[min_diff_idx]
    fib_level = levels[min_diff_idx]
    
    # Only trade if price is close to a Fibonacci level
    if min(diffs) > proximity_threshold:
        return None
    
    # Enhanced BUY conditions (bounce from lower Fib levels)
    if (entry <= closest_fib * 1.005 and fib_level <= 0.618 and 
        rsi < 70 and macd_histogram.iloc[-1] > macd_histogram.iloc[-2]):
        
        sl = low * 0.995  # Small buffer below swing low
        risk = entry - sl
        tp = entry + risk * rr_ratio
        confidence = (70 - rsi) + (1 - fib_level) * 50
        
        return {
            'name': name, 'type': 'fib', 'signal': 'buy',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'fib_level': fib_level, 'rsi': rsi, 'confidence': confidence
        }
    
    # Enhanced SELL conditions (rejection from upper Fib levels)
    if (entry >= closest_fib * 0.995 and fib_level >= 0.382 and 
        rsi > 30 and macd_histogram.iloc[-1] < macd_histogram.iloc[-2]):
        
        sl = high * 1.005  # Small buffer above swing high
        risk = sl - entry
        tp = entry - risk * rr_ratio
        confidence = rsi - 30 + fib_level * 50
        
        return {
            'name': name, 'type': 'fib', 'signal': 'sell',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'fib_level': fib_level, 'rsi': rsi, 'confidence': confidence
        }
    
    return None
