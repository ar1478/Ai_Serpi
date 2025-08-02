import pandas as pd
import numpy as np

def trend_atr(df, atr_period=14, trend_period=20, rr_ratio=2.0, volatility_filter=True):
    """
    Enhanced trend following with ATR bands and volatility filtering
    """
    name = 'Enhanced Trend+ATR'
    
    # True Range and ATR
    prev_close = df['close'].shift(1)
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low'] - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(atr_period).mean()
    
    # Trend strength using ADX concept
    plus_dm = (df['high'].diff()).where((df['high'].diff() > df['low'].diff().abs()) & (df['high'].diff() > 0), 0)
    minus_dm = (df['low'].diff().abs()).where((df['low'].diff().abs() > df['high'].diff()) & (df['low'].diff() < 0), 0)
    
    plus_di = 100 * (plus_dm.rolling(atr_period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(atr_period).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(atr_period).mean()
    
    # Bollinger Bands for volatility context
    bb_middle = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    bb_upper = bb_middle + (bb_std * 2)
    bb_lower = bb_middle - (bb_std * 2)
    
    idx = len(df) - 1
    prev = idx - 1
    current_price = df['close'].iloc[idx]
    prev_price = df['close'].iloc[prev]
    current_atr = atr.iloc[idx]
    current_adx = adx.iloc[idx]
    
    # Dynamic ATR multiplier based on volatility
    atr_multiplier = 2.0 if current_atr > atr.rolling(50).mean().iloc[idx] else 1.5
    
    upper_band = prev_price + current_atr * atr_multiplier
    lower_band = prev_price - current_atr * atr_multiplier
    
    # Enhanced BUY conditions
    if (prev_price <= upper_band and current_price > upper_band and
        current_adx > 25 and plus_di.iloc[idx] > minus_di.iloc[idx] and
        current_price > bb_middle.iloc[idx]):
        
        entry = current_price
        sl = entry - current_atr * 2
        risk = entry - sl
        tp = entry + risk * rr_ratio
        
        confidence = min(100, current_adx + (current_price - bb_middle.iloc[idx]) / bb_middle.iloc[idx] * 100)
        
        return {
            'name': name, 'type': 'atr', 'signal': 'buy',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'adx': current_adx, 'confidence': confidence, 'atr': current_atr
        }
    
    # Enhanced SELL conditions
    if (prev_price >= lower_band and current_price < lower_band and
        current_adx > 25 and minus_di.iloc[idx] > plus_di.iloc[idx] and
        current_price < bb_middle.iloc[idx]):
        
        entry = current_price
        sl = entry + current_atr * 2
        risk = sl - entry
        tp = entry - risk * rr_ratio
        
        confidence = min(100, current_adx + (bb_middle.iloc[idx] - current_price) / bb_middle.iloc[idx] * 100)
        
        return {
            'name': name, 'type': 'atr', 'signal': 'sell',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'adx': current_adx, 'confidence': confidence, 'atr': current_atr
        }
    
    return None