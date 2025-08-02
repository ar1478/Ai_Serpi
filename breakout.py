import pandas as pd
import numpy as np

def breakout(df, lookback=20, atr_period=14, min_volume_ratio=1.2, rr_ratio=2.0):
    """
    Enhanced breakout strategy with volume confirmation and dynamic ATR-based stops
    """
    name = 'Enhanced Breakout+ATR'
    
    # Calculate rolling statistics
    highs = df['high'].rolling(lookback).max()
    lows = df['low'].rolling(lookback).min()
    
    # True Range and ATR calculation
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low'] - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(atr_period).mean()
    
    # Volume confirmation
    if 'volume' in df.columns:
        avg_volume = df['volume'].rolling(20).mean()
        volume_ratio = df['volume'] / avg_volume
    else:
        volume_ratio = pd.Series([1.0] * len(df), index=df.index)
    
    idx = len(df) - 1
    prev = idx - 1
    entry = df['close'].iloc[idx]
    
    level_up = highs.iloc[prev]
    level_dn = lows.iloc[prev]
    current_atr = atr.iloc[idx]
    
    # Enhanced breakout conditions
    broke_up = (df['close'].iloc[prev] <= level_up and 
                entry > level_up and 
                (entry - level_up) > current_atr * 0.5 and
                volume_ratio.iloc[idx] >= min_volume_ratio)
    
    broke_dn = (df['close'].iloc[prev] >= level_dn and 
                entry < level_dn and 
                (level_dn - entry) > current_atr * 0.5 and
                volume_ratio.iloc[idx] >= min_volume_ratio)
    
    if broke_up:
        sl = level_up - current_atr * 0.5  # Buffer below breakout level
        risk = entry - sl
        tp = entry + risk * rr_ratio
        confidence = min(100, ((entry - level_up) / current_atr) * 20 + volume_ratio.iloc[idx] * 10)
        
        return {
            'name': name, 'type': 'breakout', 'signal': 'buy',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'confidence': confidence, 'atr': current_atr,
            'volume_ratio': volume_ratio.iloc[idx]
        }
    
    if broke_dn:
        sl = level_dn + current_atr * 0.5  # Buffer above breakdown level
        risk = sl - entry
        tp = entry - risk * rr_ratio
        confidence = min(100, ((level_dn - entry) / current_atr) * 20 + volume_ratio.iloc[idx] * 10)
        
        return {
            'name': name, 'type': 'breakout', 'signal': 'sell',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'confidence': confidence, 'atr': current_atr,
            'volume_ratio': volume_ratio.iloc[idx]
        }
    
    return None
