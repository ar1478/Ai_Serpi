import os
import time
import MetaTrader5 as mt5
import telebot
import pandas as pd
from bot_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BOT_NAME
from strategies.ma_crossover import ma_crossover
from strategies.rsi_reversal import rsi_reversal
from strategies.breakout import breakout
from strategies.trend_atr import trend_atr
from strategies.support_resistance import support_resistance
from strategies.fibonacci import fibonacci_system
from charting import plot_signal_chart
from performance_tracker import SignalPerformanceTracker

# Initialize Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Configuration
PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURJPY']
TIMEFRAMES = {
    '4H':  mt5.TIMEFRAME_H4,
    '1H':  mt5.TIMEFRAME_H1,
    '15m': mt5.TIMEFRAME_M15
}
CANDLES = 300
STRATEGIES = {
    'MA+RSI':       ma_crossover,
    'RSI Rev':      rsi_reversal,
    'Breakout':     breakout,
    'Trend+ATR':    trend_atr,
    'SupportRes':   support_resistance,
    'FibSK':        fibonacci_system
}


tracker = SignalPerformanceTracker()


def fetch_df(pair, timeframe):
    """Fetch the last CANDLES OHLC bars from MT5 for a given pair/timeframe."""
    if not mt5.initialize():
        raise RuntimeError("MT5 initialization failed")
    rates = mt5.copy_rates_from_pos(pair, timeframe, 0, CANDLES)
    mt5.shutdown()
    
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"No data received for {pair}")
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def run_all_strategies(df):
    """
    Run all strategies and return results with confidence scores
    """
    results = []
    for strategy_name, strategy_func in STRATEGIES.items():
        try:
            result = strategy_func(df)
            if result:
                # Add strategy name if not present
                if 'name' not in result:
                    result['name'] = strategy_name
                results.append(result)
        except Exception as e:
            print(f"Error in {strategy_name}: {e}")
    
    # Sort by confidence score if available, otherwise by entry price
    results.sort(key=lambda x: x.get('confidence', 50), reverse=True)
    return results

def format_signal_message(result, pair, timeframe):
    """Format trading signal for Telegram message - Fixed Markdown"""
    signal_type = result['signal'].upper()
    entry = result['entry']
    sl = result['sl']
    tp = result['tp']
    
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr_ratio = reward / risk if risk > 0 else 0
    
    # Build message with correct Markdown formatting
    message = f"🚨 *{result['name']}* Signal\n"
    message += f"📈 *Pair:* {pair}\n"
    message += f"⏰ *Timeframe:* {timeframe}\n"
    message += f"📊 *Signal:* {signal_type}\n"
    message += f"💰 *Entry:* {entry:.5f}\n"
    message += f"🛑 *Stop Loss:* {sl:.5f}\n"
    message += f"🎯 *Take Profit:* {tp:.5f}\n"
    message += f"⚖️ *R:R Ratio:* {rr_ratio:.1f}\n"
    
    # Add confidence if available
    if 'confidence' in result:
        message += f"🎯 *Confidence:* {result['confidence']:.1f}%\n"
    
    # Add additional metrics if available
    if 'rsi' in result:
        message += f"📊 *RSI:* {result['rsi']:.1f}\n"
    if 'volume_ratio' in result:
        message += f"📈 *Volume:* {result['volume_ratio']:.1f}x\n"
    if 'adx' in result:
        message += f"📉 *ADX:* {result['adx']:.1f}\n"
    
    message += f"\n🤖 *{BOT_NAME}*"
    return message

def format_signal_message_simple(result, pair, timeframe):
    """Simple text format without special formatting - Fallback"""
    signal_type = result['signal'].upper()
    entry = result['entry']
    sl = result['sl']
    tp = result['tp']
    
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr_ratio = reward / risk if risk > 0 else 0
    
    # Simple text format
    message = f"SIGNAL: {result['name']}\n"
    message += f"Pair: {pair} ({timeframe})\n"
    message += f"Direction: {signal_type}\n"
    message += f"Entry: {entry:.5f}\n"
    message += f"Stop: {sl:.5f}\n"
    message += f"Target: {tp:.5f}\n"
    message += f"R:R: {rr_ratio:.1f}\n"
    
    if 'confidence' in result:
        message += f"Confidence: {result['confidence']:.1f}%\n"
    
    if 'rsi' in result:
        message += f"RSI: {result['rsi']:.1f}\n"
    if 'volume_ratio' in result:
        message += f"Volume: {result['volume_ratio']:.1f}x\n"
    if 'adx' in result:
        message += f"ADX: {result['adx']:.1f}\n"
    
    message += f"\n{BOT_NAME}"
    return message

def send_telegram_message(message, pair, timeframe):
    """Send message to Telegram with multiple fallback options"""
    try:
        # Try with Markdown formatting first
        bot.send_message(TELEGRAM_CHAT_ID, message, parse_mode='Markdown')
        print(f"✅ Message sent to Telegram (Markdown)")
        return True
    except Exception as e:
        print(f"⚠️ Markdown failed: {e}")
        try:
            # Try with HTML formatting
            html_message = message.replace('*', '<b>').replace('*', '</b>')
            bot.send_message(TELEGRAM_CHAT_ID, html_message, parse_mode='HTML')
            print(f"✅ Message sent to Telegram (HTML)")
            return True
        except Exception as e2:
            print(f"⚠️ HTML failed: {e2}")
            try:
                # Fall back to simple text format
                simple_message = format_signal_message_simple(
                    {'name': 'Signal', 'signal': 'unknown', 'entry': 0, 'sl': 0, 'tp': 0}, 
                    pair, timeframe
                )
                bot.send_message(TELEGRAM_CHAT_ID, simple_message)
                print(f"✅ Message sent to Telegram (Plain text)")
                return True
            except Exception as e3:
                print(f"❌ All message formats failed: {e3}")
                return False

def send_chart_with_signal(pair, timeframe_name, df, result):
    """Generate and send chart with signal - Fixed for your charting.py"""
    try:
        # Your plot_signal_chart function expects: (df, signals, bot_name, pair, timeframe)
        # signals should be a list, so we wrap the single result in a list
        signals = [result]
        
        # Call your chart function with correct parameters
        chart_path = plot_signal_chart(df, signals, BOT_NAME, pair, timeframe_name)
        
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, 'rb') as photo:
                bot.send_photo(TELEGRAM_CHAT_ID, photo)
            # Clean up
            os.remove(chart_path)
            print(f"✅ Chart sent for {pair} {timeframe_name}")
            return True
        else:
            print(f"⚠️ No chart file generated for {pair} {timeframe_name}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send chart for {pair} {timeframe_name}: {e}")
        return False

def process_pair_timeframe(pair, timeframe_name, timeframe_mt5):
    """Process a single pair/timeframe combination"""
    try:
        print(f"📊 Analyzing {pair} {timeframe_name}...")
        df = fetch_df(pair, timeframe_mt5)
        
        if df is None or len(df) < 50:
            print(f"⚠️ Insufficient data for {pair} {timeframe_name}")
            return
        
        results = run_all_strategies(df)
        
        if results:
            print(f"🎯 Found {len(results)} signal(s) for {pair} {timeframe_name}")
            
            # Send only the highest confidence signal
            best_result = results[0]
            
            # Format and send message
            message = format_signal_message(best_result, pair, timeframe_name)
            message_sent = send_telegram_message(message, pair, timeframe_name)
            
            # Send chart if message was sent successfully
            if message_sent:
                send_chart_with_signal(pair, timeframe_name, df, best_result)
                
        else:
            print(f"📭 No signals for {pair} {timeframe_name}")
            
    except Exception as e:
        print(f"❌ Error processing {pair} {timeframe_name}: {e}")

def run_all():
    """Main function to run all analysis"""
    print(f"\n🚀 Starting analysis at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    signals_sent = 0
    
    for pair in PAIRS:
        for timeframe_name, timeframe_mt5 in TIMEFRAMES.items():
            try:
                process_pair_timeframe(pair, timeframe_name, timeframe_mt5)
                # Small delay between requests to avoid rate limiting
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error with {pair} {timeframe_name}: {e}")
    
    print("=" * 60)
    print(f"✅ Analysis completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")

def test_single_pair():
    """Test function for debugging"""
    pair = 'EURUSD'
    timeframe = mt5.TIMEFRAME_H1
    
    try:
        print(f"Testing {pair} on 1H timeframe...")
        df = fetch_df(pair, timeframe)
        print(f"Fetched {len(df)} candles for {pair}")
        
        results = run_all_strategies(df)
        
        if results:
            print(f"\nFound {len(results)} signals:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['name']}")
                print(f"   Signal: {result['signal'].upper()}")
                print(f"   Entry: {result['entry']:.5f}")
                print(f"   Stop Loss: {result['sl']:.5f}")
                print(f"   Take Profit: {result['tp']:.5f}")
                if 'confidence' in result:
                    print(f"   Confidence: {result['confidence']:.1f}%")
            
            # Test message formatting
            best_result = results[0]
            message = format_signal_message(best_result, pair, '1H')
            print(f"\nFormatted message:\n{message}")
            
            # Test sending (uncomment to actually send)
            # send_telegram_message(message, pair, '1H')
            
        else:
            print("No signals found")
            
    except Exception as e:
        print(f"Error in test: {e}")

def test_telegram_connection():
    """Test Telegram bot connection"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, f"🤖 {BOT_NAME} - Connection Test ✅")
        print("✅ Telegram connection successful")
        return True
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")
        return False

if __name__ == '__main__':
    print(f"🤖 Starting {BOT_NAME}...")
    
    # Test MT5 connection first
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        exit(1)
    else:
        print("✅ MT5 initialized successfully")
        mt5.shutdown()
    
    # Test Telegram connection
    if not test_telegram_connection():
        print("❌ Telegram connection failed - check your bot token and chat ID")
        exit(1)
    
    # Uncomment for testing single pair
    # test_single_pair()
    # exit()
    
    print(f"🤖 {BOT_NAME} is running and will send signals every hour...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            run_all()
            print(f"⏰ Waiting 1 hour until next scan...")
            time.sleep(3600)  # wait 1 hour before next batch
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        # Send error notification
        try:
            bot.send_message(TELEGRAM_CHAT_ID, f"🚨 {BOT_NAME} Error: {str(e)[:200]}")
        except:
            pass