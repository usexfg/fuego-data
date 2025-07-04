#!/usr/bin/env python3
"""
XFG/BTC to XFG/USD Converter
Converts XFG/BTC price data to XFG/USD by fetching historical BTC/USD prices
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime
from typing import Dict, List, Any

def load_xfg_btc_data(filename: str) -> List[Dict]:
    """Load XFG/BTC data from JSON file"""
    print(f"Loading XFG/BTC data from {filename}...")
    
    with open(filename, 'r') as f:
        content = f.read().strip()
    
    # Parse each line as a separate JSON object
    data_points = []
    for line in content.split('\n'):
        line = line.strip()
        if line:
            try:
                data_points.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Error parsing line: {line[:50]}... - {e}")
    
    print(f"✓ Loaded {len(data_points)} XFG/BTC data points")
    return data_points

def get_btc_price_at_timestamp(timestamp: int, btc_cache: Dict[str, float]) -> float:
    """Get BTC/USD price at specific timestamp with caching"""
    # Convert timestamp to date string for caching
    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    
    if date_str in btc_cache:
        return btc_cache[date_str]
    
    try:
        # Use CoinGecko API for historical BTC price
        # Convert timestamp to seconds if needed
        if timestamp > 10**10:  # If timestamp is in milliseconds
            timestamp = timestamp // 1000
        
        # Get date in required format
        date_obj = datetime.fromtimestamp(timestamp)
        date_str_api = date_obj.strftime('%d-%m-%Y')
        
        print(f"Fetching BTC price for {date_str} (timestamp: {timestamp})...")
        
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={date_str_api}"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                btc_price = data['market_data']['current_price']['usd']
                btc_cache[date_str] = btc_price
                print(f"✓ BTC price on {date_str}: ${btc_price:.2f}")
                return btc_price
            else:
                print(f"✗ Failed to fetch BTC price for {date_str}: {response.status}")
                return None
                
    except Exception as e:
        print(f"✗ Error fetching BTC price for {date_str}: {e}")
        return None

def get_all_btc_prices_bulk(timestamps: List[int]) -> Dict[str, float]:
    """Get all BTC prices efficiently using bulk API calls"""
    print("Fetching BTC historical prices in bulk...")
    btc_cache = {}
    
    try:
        # Get the date range
        start_timestamp = min(timestamps)
        end_timestamp = max(timestamps)
        
        # Convert to dates
        start_date = datetime.fromtimestamp(start_timestamp)
        end_date = datetime.fromtimestamp(end_timestamp)
        
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Calculate days between start and end
        days_diff = (end_timestamp - start_timestamp) // (24 * 3600) + 30  # Add buffer
        
        # Use CoinGecko market chart API for bulk data
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days_diff}&interval=daily"
        
        print(f"Fetching BTC market chart for {days_diff} days...")
        
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                prices = data.get('prices', [])
                
                print(f"✓ Received {len(prices)} BTC price points")
                
                # Build cache from bulk data
                for timestamp_ms, price in prices:
                    date_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
                    btc_cache[date_str] = price
                
                print(f"✓ Built BTC price cache with {len(btc_cache)} entries")
                return btc_cache
            else:
                print(f"✗ Bulk BTC fetch failed: {response.status}")
                
    except Exception as e:
        print(f"✗ Bulk BTC fetch error: {e}")
    
    return btc_cache

def convert_xfg_to_usd(xfg_btc_data: List[Dict]) -> List[Dict]:
    """Convert XFG/BTC data to XFG/USD"""
    print("Converting XFG/BTC to XFG/USD...")
    
    # Extract all timestamps
    timestamps = [item['period_start'] for item in xfg_btc_data]
    
    # Get BTC prices in bulk
    btc_cache = get_all_btc_prices_bulk(timestamps)
    
    converted_data = []
    successful_conversions = 0
    failed_conversions = 0
    
    for item in xfg_btc_data:
        timestamp = item['period_start']
        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        # Get BTC price for this date
        btc_price = btc_cache.get(date_str)
        
        if btc_price is None:
            # Fallback to individual API call
            btc_price = get_btc_price_at_timestamp(timestamp, btc_cache)
            if btc_price:
                time.sleep(0.1)  # Rate limiting
        
        if btc_price:
            # Convert XFG/BTC prices to XFG/USD
            converted_item = {
                'period_start': item['period_start'],
                'open': str(float(item['open']) * btc_price),
                'high': str(float(item['high']) * btc_price),
                'low': str(float(item['low']) * btc_price),
                'close': str(float(item['close']) * btc_price),
                'volume': item['volume']  # Keep volume as is
            }
            converted_data.append(converted_item)
            successful_conversions += 1
            
            if successful_conversions % 10 == 0:
                print(f"Converted {successful_conversions} data points...")
        else:
            print(f"✗ Skipping {date_str} - no BTC price available")
            failed_conversions += 1
    
    print(f"✓ Conversion complete: {successful_conversions} successful, {failed_conversions} failed")
    return converted_data

def save_xfg_usd_data(data: List[Dict], filename: str):
    """Save XFG/USD data in the same format as original"""
    print(f"Saving XFG/USD data to {filename}...")
    
    with open(filename, 'w') as f:
        for item in data:
            # Format exactly like the original file (one JSON object per line)
            json_line = json.dumps(item, separators=(',', ': '))
            f.write(json_line + '\n')
    
    print(f"✓ Saved {len(data)} XFG/USD data points to {filename}")

def main():
    """Main conversion process"""
    print("🔥 XFG/BTC to XFG/USD Converter Starting...")
    print("=" * 60)
    
    try:
        # Load XFG/BTC data
        xfg_btc_data = load_xfg_btc_data('xfg-btc-data.json')
        
        if not xfg_btc_data:
            print("✗ No XFG/BTC data loaded")
            return
        
        # Show sample data
        print("\nSample XFG/BTC data:")
        for i, item in enumerate(xfg_btc_data[:3]):
            date_str = datetime.fromtimestamp(item['period_start']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {i+1}. {date_str} - Close: {item['close']} BTC")
        
        print(f"\nTime range: {datetime.fromtimestamp(xfg_btc_data[0]['period_start']).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(xfg_btc_data[-1]['period_start']).strftime('%Y-%m-%d')}")
        
        # Convert to USD
        xfg_usd_data = convert_xfg_to_usd(xfg_btc_data)
        
        if xfg_usd_data:
            # Save converted data
            save_xfg_usd_data(xfg_usd_data, 'xfg-usd-data.json')
            
            # Show sample converted data
            print("\nSample XFG/USD data:")
            for i, item in enumerate(xfg_usd_data[:3]):
                date_str = datetime.fromtimestamp(item['period_start']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {i+1}. {date_str} - Close: ${float(item['close']):.8f} USD")
            
            print(f"\n✓ Successfully converted {len(xfg_usd_data)} data points!")
            print(f"✓ Output file: xfg-usd-data.json")
        else:
            print("✗ No data was successfully converted")
    
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 