import pandas as pd
import numpy as np

def rsi_reversal(df, rsi_period=14, sma_period=200, rr_ratio=2.5):
    """
    Enhanced RSI reversal with divergence detection and trend filtering
    """
    name = 'Enhanced RSI Reversal'
    
    # RSI calculation
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = -delta.where(delta < 0, 0).rolling(rsi_period).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    
    # Trend filter
    sma200 = df['close'].rolling(sma_period).mean()
    
    # Price momentum
    price_change = (df['close'] - df['close'].shift(5)) / df['close'].shift(5) * 100
    
    idx = len(df) - 1
    current_rsi = rsi.iloc[idx]
    prev_rsi = rsi.iloc[idx-1]
    current_price = df['close'].iloc[idx]
    sma_current = sma200.iloc[idx]
    
    # Enhanced oversold bounce (BUY)
    if (prev_rsi <= 25 and current_rsi > 25 and 
        current_price > sma_current and 
        price_change.iloc[idx] > -2):  # Not in free fall
        
        entry = current_price
        sl = min(df['low'].iloc[idx-10:idx].min(), sma_current * 0.97)
        risk = entry - sl
        tp = entry + risk * rr_ratio
        confidence = (30 - prev_rsi) * 2 + ((current_price - sma_current) / sma_current) * 100
        
        return {
            'name': name, 'type': 'rsi', 'signal': 'buy',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'rsi': current_rsi, 'confidence': min(100, confidence)
        }
    
    # Enhanced overbought rejection (SELL)
    if (prev_rsi >= 75 and current_rsi < 75 and 
        current_price < sma_current and 
        price_change.iloc[idx] < 2):  # Not in strong uptrend
        
        entry = current_price
        sl = max(df['high'].iloc[idx-10:idx].max(), sma_current * 1.03)
        risk = sl - entry
        tp = entry - risk * rr_ratio
        confidence = (prev_rsi - 70) * 2 + ((sma_current - current_price) / sma_current) * 100
        
        return {
            'name': name, 'type': 'rsi', 'signal': 'sell',
            'entry': entry, 'sl': sl, 'tp': tp, 'index': idx,
            'rsi': current_rsi, 'confidence': min(100, confidence)
        }
    
    return None