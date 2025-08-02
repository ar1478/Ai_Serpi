# charting.py - Optional improvements (current version works fine!)
import mplfinance as mpf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import os

def plot_signal_chart(df, signals, bot_name, pair, timeframe):
    """
    Generate trading signal chart with optional improvements
    """
    try:
        # Ensure we have data
        if df is None or len(df) == 0:
            print("⚠️ No data provided for chart")
            return None
            
        if not signals:
            print("⚠️ No signals provided for chart")
            return None
        
        # Set up dataframe for plotting
        df_plot = df.set_index('time') if 'time' in df.columns else df.copy()
        df_plot = df_plot.iloc[-60:]  # Zoom into last 60 candles
        
        if len(df_plot) == 0:
            print("⚠️ No data after filtering for chart")
            return None
        
        addplots = []
        annotations = []
        
        # Process each signal
        for s in signals:
            try:
                idx = s.get('index', len(df_plot) - 1)
                
                # Get timestamp - use last available if index is out of range
                if idx >= len(df_plot):
                    ts = df_plot.index[-1]
                else:
                    ts = df_plot.index[idx] if idx < len(df_plot.index) else df_plot.index[-1]
                
                entry_val = float(s['entry'])
                sl_val = float(s['sl'])
                tp_val = float(s['tp'])
                signal_type = s['signal'].lower()
                strategy = s.get('name', 'Unknown Strategy')
                
                # Entry line (orange)
                entry_line = pd.Series(np.nan, index=df_plot.index)
                entry_line.loc[ts] = entry_val
                addplots.append(mpf.make_addplot(entry_line, type='scatter', marker='o', color='orange', markersize=80))
                addplots.append(mpf.make_addplot(entry_line, type='line', linestyle='-', color='orange', width=2))
                
                # SL (red dashed line)
                sl_line = pd.Series(np.nan, index=df_plot.index)
                sl_line.loc[ts] = sl_val
                addplots.append(mpf.make_addplot(sl_line, type='line', linestyle='--', color='red', width=2))
                
                # TP (green dashed line)
                tp_line = pd.Series(np.nan, index=df_plot.index)
                tp_line.loc[ts] = tp_val
                addplots.append(mpf.make_addplot(tp_line, type='line', linestyle='--', color='green', width=2))
                
                # Signal arrow marker
                marker = '^' if signal_type == 'buy' else 'v'
                color = 'lime' if signal_type == 'buy' else 'red'
                mark = pd.Series(np.nan, index=df_plot.index)
                mark.loc[ts] = entry_val
                addplots.append(mpf.make_addplot(mark, type='scatter', marker=marker, color=color, markersize=150))
                
                # Store annotation info
                annotations.append({
                    'ts': ts, 'entry': entry_val, 'sl': sl_val, 'tp': tp_val,
                    'strategy': strategy, 'type': signal_type.upper(),
                    'confidence': s.get('confidence', 0)
                })
                
            except Exception as e:
                print(f"⚠️ Error processing signal: {e}")
                continue
        
        if not addplots:
            print("⚠️ No valid signals to plot")
            return None
        
        # Create the plot
        fig, axlist = mpf.plot(
            df_plot,
            type='candle',
            style='charles',
            title=f"{bot_name} | {pair} {timeframe} | {len(signals)} Signal(s)",
            addplot=addplots,
            volume=False,
            returnfig=True,
            figsize=(14, 8),
            tight_layout=True
        )
        
        ax = axlist[0]
        
        # Add annotations for each signal
        for i, ann in enumerate(annotations):
            try:
                x = ann['ts']
                y = ann['entry']
                
                # Main signal label
                label_text = f"{ann['type']} - {ann['strategy']}"
                if ann['confidence'] > 0:
                    label_text += f" ({ann['confidence']:.0f}%)"
                
                # Position label above/below based on signal type
                y_offset = 0.002 if ann['type'] == 'BUY' else -0.002
                
                ax.annotate(label_text, 
                           xy=(x, y),
                           xytext=(x, y + y_offset),
                           fontsize=9, 
                           fontweight='bold', 
                           color='darkblue',
                           ha='center',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7),
                           arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
                
                # Price level labels
                ax.annotate(f"Entry: {ann['entry']:.5f}", 
                           xy=(x, y), 
                           xytext=(x, y + 0.0008), 
                           fontsize=8, 
                           color='darkorange', 
                           ha='center',
                           fontweight='bold')
                
                ax.annotate(f"SL: {ann['sl']:.5f}", 
                           xy=(x, ann['sl']), 
                           xytext=(x, ann['sl'] - 0.0008), 
                           fontsize=8, 
                           color='darkred', 
                           ha='center',
                           fontweight='bold')
                
                ax.annotate(f"TP: {ann['tp']:.5f}", 
                           xy=(x, ann['tp']), 
                           xytext=(x, ann['tp'] + 0.0008), 
                           fontsize=8, 
                           color='darkgreen', 
                           ha='center',
                           fontweight='bold')
                
            except Exception as e:
                print(f"⚠️ Error adding annotation {i}: {e}")
                continue
        
        # Create unique filename
        timestamp = int(time.time())
        filename = f"chart_{pair}_{timeframe}_{timestamp}.png"
        
        # Save with high quality
        fig.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        # Verify file was created
        if os.path.exists(filename):
            print(f"📊 Chart saved: {filename}")
            return filename
        else:
            print(f"❌ Failed to save chart: {filename}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating chart: {e}")
        return None


# Alternative simple version if you prefer minimal changes to your current code
def plot_signal_chart_simple(df, signals, bot_name, pair, timeframe):
    """
    Your original function with just error handling added
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch
        import mplfinance as mpf
        
        df_plot = df.set_index('time')
        df_plot = df_plot.iloc[-60:]  # Zoom into last 60 candles
        addplots = []
        annotations = []
        
        for s in signals:
            idx = s['index']
            ts = df_plot.index[-1] if idx >= len(df_plot) else df_plot.index[idx]
            entry_val = s['entry']
            sl_val = s['sl']
            tp_val = s['tp']
            signal_type = s['signal']
            strategy = s.get('name', '')
            
            # Entry line (orange)
            entry_line = pd.Series(np.nan, index=df_plot.index)
            entry_line.loc[ts] = entry_val
            addplots.append(mpf.make_addplot(entry_line, type='scatter', marker='o', color='orange', markersize=80))
            addplots.append(mpf.make_addplot(entry_line, type='line', linestyle='-', color='orange'))
            
            # SL (red)
            sl_line = pd.Series(np.nan, index=df_plot.index)
            sl_line.loc[ts] = sl_val
            addplots.append(mpf.make_addplot(sl_line, type='line', linestyle='--', color='red'))
            
            # TP (green)
            tp_line = pd.Series(np.nan, index=df_plot.index)
            tp_line.loc[ts] = tp_val
            addplots.append(mpf.make_addplot(tp_line, type='line', linestyle='--', color='green'))
            
            # Marker
            marker = '^' if signal_type == 'buy' else 'v'
            color = 'green' if signal_type == 'buy' else 'red'
            mark = pd.Series(np.nan, index=df_plot.index)
            mark.loc[ts] = entry_val
            addplots.append(mpf.make_addplot(mark, type='scatter', marker=marker, color=color, markersize=150))
            
            annotations.append({
                'ts': ts, 'entry': entry_val, 'sl': sl_val, 'tp': tp_val,
                'strategy': strategy, 'type': signal_type.upper()
            })
        
        # Plot it
        fig, axlist = mpf.plot(
            df_plot,
            type='candle',
            style='charles',
            title=f"{bot_name} | {pair} {timeframe}",
            addplot=addplots,
            volume=False,
            returnfig=True,
            figsize=(14, 8),
            tight_layout=True
        )
        
        ax = axlist[0]
        
        # Annotate for each signal
        for ann in annotations:
            x = ann['ts']
            y = ann['entry']
            ax.annotate(f"{ann['type']} - {ann['strategy']}", xy=(x, y),
                        xytext=(x, y + 0.001 if ann['type'] == 'BUY' else y - 0.001),
                        fontsize=9, fontweight='bold', color='blue',
                        arrowprops=dict(arrowstyle='->', color='blue'))
            ax.annotate("Entry", xy=(x, y), xytext=(x, y + 0.0005), fontsize=8, color='orange', ha='center')
            ax.annotate("SL", xy=(x, ann['sl']), xytext=(x, ann['sl'] - 0.0005), fontsize=8, color='red', ha='center')
            ax.annotate("TP", xy=(x, ann['tp']), xytext=(x, ann['tp'] + 0.0005), fontsize=8, color='green', ha='center')
        
        filename = f"chart_{pair}_{timeframe}_{int(time.time())}.png"
        fig.savefig(filename, dpi=150)
        plt.close(fig)
        return filename
        
    except Exception as e:
        print(f"❌ Chart generation error: {e}")
        return None