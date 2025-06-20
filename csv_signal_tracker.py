#!/usr/bin/env python3
"""
CSV Signal History Tracker for Feature 02 completion
Simple CSV-based signal change tracking
"""

import pandas as pd
import os
from datetime import datetime
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

class SignalHistoryTracker:
    """Simple CSV-based signal history tracking"""
    
    def __init__(self, csv_file="data/signal_history.csv"):
        self.csv_file = csv_file
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        
    def track_signal_change(self, symbol, old_signal, new_signal, confidence_score, reasoning=""):
        """Track signal changes to CSV file"""
        
        # Prepare signal change record
        record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'old_signal': old_signal,
            'new_signal': new_signal,
            'confidence_score': confidence_score,
            'signal_change': f"{old_signal} -> {new_signal}",
            'reasoning': reasoning
        }
        
        # Convert to DataFrame
        df = pd.DataFrame([record])
        
        # Append to existing CSV or create new one
        if os.path.exists(self.csv_file):
            df.to_csv(self.csv_file, mode='a', header=False, index=False)
        else:
            df.to_csv(self.csv_file, index=False)
            
        print(f"✅ Signal change tracked: {symbol} {old_signal} -> {new_signal}")
        
    def get_recent_changes(self, days=7):
        """Get recent signal changes"""
        if not os.path.exists(self.csv_file):
            return pd.DataFrame()
            
        df = pd.read_csv(self.csv_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter to recent days
        cutoff = datetime.now() - pd.Timedelta(days=days)
        recent = df[df['timestamp'] >= cutoff]
        
        return recent.sort_values('timestamp', ascending=False)
        
    def get_signal_stats(self):
        """Get basic signal change statistics"""
        if not os.path.exists(self.csv_file):
            return {"total_changes": 0}
            
        df = pd.read_csv(self.csv_file)
        
        stats = {
            'total_changes': len(df),
            'unique_symbols': df['symbol'].nunique() if len(df) > 0 else 0,
            'avg_confidence': df['confidence_score'].mean() if len(df) > 0 else 0,
            'most_active_symbol': df['symbol'].value_counts().index[0] if len(df) > 0 else None
        }
        
        return stats

def demo_signal_tracking():
    """Demonstrate CSV signal tracking functionality"""
    print("🧪 Testing CSV Signal History Tracking")
    print("=" * 50)
    
    tracker = SignalHistoryTracker()
    
    # Demo signal changes
    demo_changes = [
        ("NVDA", "WATCH", "SOON", 6.5, "Bond volatility increasing"),
        ("AMD", "NEUTRAL", "WATCH", 5.8, "Yield curve inversion detected"),
        ("TSM", "SOON", "NOW", 8.2, "High correlation signal triggered"),
        ("NVDA", "SOON", "NOW", 8.7, "Multiple indicators confirming"),
        ("AMD", "WATCH", "SOON", 7.1, "Credit spreads widening")
    ]
    
    print("\n📊 Tracking Signal Changes:")
    for symbol, old_sig, new_sig, conf, reason in demo_changes:
        tracker.track_signal_change(symbol, old_sig, new_sig, conf, reason)
    
    print(f"\n📈 Recent Signal Changes (Last 7 Days):")
    recent = tracker.get_recent_changes()
    if not recent.empty:
        print(recent[['timestamp', 'symbol', 'signal_change', 'confidence_score']].to_string(index=False))
    
    print(f"\n📊 Signal Change Statistics:")
    stats = tracker.get_signal_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n✅ CSV Signal History Tracking: IMPLEMENTED")
    print(f"  📁 File: {tracker.csv_file}")
    print(f"  📈 Records: {stats['total_changes']}")
    print(f"  📊 Symbols: {stats['unique_symbols']}")

if __name__ == "__main__":
    demo_signal_tracking()
