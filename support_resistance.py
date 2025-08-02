import pandas as pd
import numpy as np

def support_resistance(df, lookback=50, proximity_pct=0.008, rr_ratio=2.0):
    """
    Enhanced support/resistance with multiple timeframe analysis
    """
    name = 'Enhanced Support/Resistance'
    
    # Multiple timeframe levels
    short_high = df['high'].rolling(lookback//2).max().iloc[-1]
    short_low = df['low'].rolling(lookback//2).min().iloc[-1]
    long_high = df['high'].rolling(lookback).max().iloc[-1]
    long_low = df['low'].rolling(lookback).min().iloc[-1]
    
    current_price = df['close'].iloc[-1]
    idx = len(df) - 1
    
    # ATR for dynamic stops
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low'] - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    
    # RSI for momentum
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rsi = (100 - (100 / (1 + gain/loss))).iloc[-1]
    
    # Test multiple resistance levels for SELL
    resistance_levels = [long_high, short_high]
    for resistance in resistance_levels:
        if (abs(current_price - resistance) / resistance <= proximity_pct and 
            current_price >= resistance * 0.998 and rsi > 60):
            
            entry = current_price
            sl = resistance + atr * 1.5
            risk = sl - entry
            tp = entry - risk * rr_ratio
            
            # Confidence based on how close to resistance and RSI level
            proximity_score = (1 - abs(current_price - resistance) / resistance) * 50
            rsi_score = min(40, rsi - 60)
            confidence = proximity_score + rsi_score
            
            return {
                'name': name, 'type': 'sr', 'signal': 'sell',
                'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
                'level': resistance, 'rsi': rsi, 'confidence': confidence
            }
    
    # Test multiple support levels for BUY
    support_levels = [long_low, short_low]
    for support in support_levels:
        if (abs(current_price - support) / support <= proximity_pct and 
            current_price <= support * 1.002 and rsi < 40):
            
            entry = current_price
            sl = support - atr * 1.5
            risk = entry - sl
            tp = entry + risk * rr_ratio
            
            # Confidence based on how close to support and RSI level
            proximity_score = (1 - abs(current_price - support) / support) * 50
            rsi_score = min(40, 40 - rsi)
            confidence = proximity_score + rsi_score
            
            return {
                'name': name, 'type': 'sr', 'signal': 'buy',
                'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
                'level': support, 'rsi': rsi, 'confidence': confidence
            }
    
    return None
