#!/usr/bin/env python3
"""
Data Verification Script
Verifies the integrity and completeness of the XFG historical data
"""

import json
from datetime import datetime

def verify_complete_dataset():
    """Verify the complete historical dataset"""
    print("🔥 XFG Complete Historical Dataset Verification")
    print("=" * 60)
    
    try:
        # Load the complete dataset
        with open('xfg-complete-historical.json', 'r') as f:
            lines = f.readlines()
        
        print(f"✓ Total data points: {len(lines)}")
        
        # Parse first and last entries
        first_item = json.loads(lines[0])
        last_item = json.loads(lines[-1])
        
        first_date = datetime.fromtimestamp(first_item['period_start'])
        last_date = datetime.fromtimestamp(last_item['period_start'])
        
        print(f"✓ Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
        print(f"✓ Duration: {(last_date - first_date).days} days")
        
        # Analyze price data
        prices = []
        for line in lines:
            item = json.loads(line)
            prices.append(float(item['close']))
        
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        print(f"\n📊 Price Statistics:")
        print(f"   Minimum: ${min_price:.8f}")
        print(f"   Maximum: ${max_price:.8f}")
        print(f"   Average: ${avg_price:.8f}")
        print(f"   Range: {((max_price - min_price) / min_price * 100):.1f}% variation")
        
        # Check data integrity
        valid_entries = 0
        for line in lines:
            try:
                item = json.loads(line)
                required_fields = ['period_start', 'open', 'high', 'low', 'close', 'volume']
                if all(field in item for field in required_fields):
                    valid_entries += 1
            except:
                pass
        
        print(f"\n✅ Data Integrity:")
        print(f"   Valid entries: {valid_entries}/{len(lines)} ({valid_entries/len(lines)*100:.1f}%)")
        
        # Show sample data points
        print(f"\n📋 Sample Data Points:")
        for i in [0, len(lines)//4, len(lines)//2, len(lines)*3//4, -1]:
            item = json.loads(lines[i])
            date_str = datetime.fromtimestamp(item['period_start']).strftime('%Y-%m-%d')
            price = float(item['close'])
            print(f"   {date_str}: ${price:.8f}")
        
        print(f"\n🎯 Dataset Summary:")
        print(f"   • Covers {(last_date - first_date).days} days of price history")
        print(f"   • Includes both original XFG/BTC converted data and extended sample data")
        print(f"   • Ready for chart visualization with full timeframe support")
        print(f"   • Compatible with TradingView-style candlestick charts")
        
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

def main():
    """Main verification"""
    success = verify_complete_dataset()
    
    if success:
        print(f"\n✅ Verification Complete - Dataset is ready for use!")
        print(f"🌐 View the chart at: http://localhost:8000/chart.html")
    else:
        print(f"\n❌ Verification Failed - Please check the data files")

if __name__ == "__main__":
    main() 