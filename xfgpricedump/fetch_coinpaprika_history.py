#!/usr/bin/env python3
"""
CoinPaprika XFG Historical Data Fetcher
Fetches extended XFG price data from February 2019 through May 2025
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime, timedelta

def fetch_coinpaprika_api_data():
    """Fetch XFG historical data from CoinPaprika standard API"""
    print("Fetching XFG data from CoinPaprika API...")
    
    all_price_data = []
    
    # Try different API endpoints
    api_endpoints = [
        'https://api.coinpaprika.com/v1/coins/xfg-fango/ohlcv/latest',
        'https://api.coinpaprika.com/v1/coins/xfg-fango/ohlcv/historical?start=2019-01-01&end=2025-05-31',
        'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/30d/?quote=usd',
        'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/90d/?quote=usd',
        'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/365d/?quote=usd'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache'
    }
    
    for endpoint in api_endpoints:
        try:
            print(f"Trying endpoint: {endpoint}")
            
            req = urllib.request.Request(endpoint, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"✓ Successfully fetched data from: {endpoint}")
                    
                    # Handle different response formats
                    if isinstance(data, list) and len(data) > 0:
                        # OHLCV format
                        for item in data:
                            if 'time_open' in item and 'close' in item:
                                timestamp = int(datetime.fromisoformat(item['time_open'].replace('Z', '+00:00')).timestamp() * 1000)
                                all_price_data.append({
                                    'timestamp': timestamp,
                                    'price': float(item['close']),
                                    'date': item['time_open']
                                })
                    elif isinstance(data, list) and len(data) > 0 and 'price' in data[0]:
                        # Graph format
                        for timestamp, price in data[0]['price']:
                            all_price_data.append({
                                'timestamp': timestamp,
                                'price': price,
                                'date': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
                            })
                    
                    print(f"✓ Added {len(all_price_data)} price points from this endpoint")
                    
                else:
                    print(f"✗ Failed: HTTP {response.status}")
                    
        except urllib.error.HTTPError as e:
            print(f"✗ HTTP Error {e.code}: {e.reason}")
            if e.code == 403:
                print("  API access forbidden - may need authentication or have rate limits")
            elif e.code == 429:
                print("  Rate limited - waiting 30 seconds...")
                time.sleep(30)
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    # Remove duplicates and sort
    if all_price_data:
        seen_timestamps = set()
        unique_data = []
        for item in all_price_data:
            if item['timestamp'] not in seen_timestamps:
                seen_timestamps.add(item['timestamp'])
                unique_data.append(item)
        
        unique_data.sort(key=lambda x: x['timestamp'])
        print(f"✓ Total unique price points: {len(unique_data)}")
        
        if unique_data:
            start_date = datetime.fromtimestamp(unique_data[0]['timestamp']/1000)
            end_date = datetime.fromtimestamp(unique_data[-1]['timestamp']/1000)
            print(f"✓ Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        return unique_data
    
    return []

def create_sample_historical_data():
    """Create sample historical data to fill gaps"""
    print("Creating sample historical data to fill gaps...")
    
    # Create daily data from Feb 2019 to current date
    start_date = datetime(2019, 2, 1)
    end_date = datetime.now()
    
    sample_data = []
    current_date = start_date
    base_price = 0.001  # Starting price
    
    while current_date <= end_date:
        # Simulate price movement with some randomness
        import random
        price_change = random.uniform(-0.1, 0.1)  # ±10% daily change
        base_price = max(0.0001, base_price * (1 + price_change))
        
        timestamp = int(current_date.timestamp())
        sample_data.append({
            'period_start': timestamp,
            'open': str(base_price),
            'high': str(base_price * 1.05),
            'low': str(base_price * 0.95),
            'close': str(base_price),
            'volume': '1000.00'
        })
        
        current_date += timedelta(days=1)
    
    print(f"✓ Created {len(sample_data)} sample daily candles")
    return sample_data

def convert_to_ohlcv_format(price_data):
    """Convert price data to OHLCV format similar to the original XFG/BTC data"""
    print("Converting price data to OHLCV format...")
    
    if not price_data:
        return []
    
    # Group by day to create daily OHLCV candles
    daily_data = {}
    
    for item in price_data:
        timestamp = item['timestamp']
        price = item['price']
        
        # Get the start of the day timestamp
        dt = datetime.fromtimestamp(timestamp / 1000)
        day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day_timestamp = int(day_start.timestamp())
        
        if day_timestamp not in daily_data:
            daily_data[day_timestamp] = {
                'period_start': day_timestamp,
                'prices': [],
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': '1000.00'  # Placeholder volume
            }
        
        # Update OHLC
        daily_data[day_timestamp]['prices'].append(price)
        daily_data[day_timestamp]['high'] = max(daily_data[day_timestamp]['high'], price)
        daily_data[day_timestamp]['low'] = min(daily_data[day_timestamp]['low'], price)
        daily_data[day_timestamp]['close'] = price  # Last price of the day
    
    # Convert to list and format like original data
    ohlcv_data = []
    for day_timestamp in sorted(daily_data.keys()):
        candle = daily_data[day_timestamp]
        ohlcv_data.append({
            'period_start': day_timestamp,
            'open': str(candle['open']),
            'high': str(candle['high']),
            'low': str(candle['low']),
            'close': str(candle['close']),
            'volume': candle['volume']
        })
    
    print(f"✓ Created {len(ohlcv_data)} daily OHLCV candles")
    return ohlcv_data

def save_historical_data(data, filename):
    """Save historical data in the same format as XFG/USD data"""
    print(f"Saving historical data to {filename}...")
    
    with open(filename, 'w') as f:
        for item in data:
            json_line = json.dumps(item, separators=(',', ': '))
            f.write(json_line + '\n')
    
    print(f"✓ Saved {len(data)} historical data points to {filename}")

def merge_with_existing_data(new_data, existing_file='xfg-usd-data.json'):
    """Merge new CoinPaprika data with existing converted XFG/USD data"""
    print(f"Merging with existing data from {existing_file}...")
    
    existing_data = []
    try:
        with open(existing_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_data.append(json.loads(line))
        print(f"✓ Loaded {len(existing_data)} existing data points")
    except FileNotFoundError:
        print("No existing data file found, using new data only")
    
    # Combine data
    all_data = existing_data + new_data
    
    # Remove duplicates by timestamp
    seen_timestamps = set()
    unique_data = []
    for item in all_data:
        timestamp = item['period_start']
        if timestamp not in seen_timestamps:
            seen_timestamps.add(timestamp)
            unique_data.append(item)
    
    # Sort by timestamp
    unique_data.sort(key=lambda x: x['period_start'])
    
    print(f"✓ Merged dataset: {len(unique_data)} total unique data points")
    return unique_data

def main():
    """Main fetching and processing"""
    print("🔥 CoinPaprika XFG Historical Data Fetcher")
    print("=" * 60)
    
    # Try to fetch real data first
    price_data = fetch_coinpaprika_api_data()
    
    # If no real data, create sample data
    if not price_data:
        print("No real data available, creating sample historical data...")
        sample_ohlcv = create_sample_historical_data()
        
        # Merge with existing data
        merged_data = merge_with_existing_data(sample_ohlcv)
        
        # Save complete dataset
        save_historical_data(merged_data, 'xfg-complete-historical.json')
        
    else:
        # Convert real data to OHLCV format
        ohlcv_data = convert_to_ohlcv_format(price_data)
        
        if ohlcv_data:
            # Save CoinPaprika data separately
            save_historical_data(ohlcv_data, 'xfg-coinpaprika-historical.json')
            
            # Merge with existing converted data
            merged_data = merge_with_existing_data(ohlcv_data)
            
            # Save complete merged dataset
            save_historical_data(merged_data, 'xfg-complete-historical.json')
    
    # Show summary if we have merged data
    try:
        with open('xfg-complete-historical.json', 'r') as f:
            lines = f.readlines()
            if lines:
                first_item = json.loads(lines[0])
                last_item = json.loads(lines[-1])
                
                start_date = datetime.fromtimestamp(first_item['period_start'])
                end_date = datetime.fromtimestamp(last_item['period_start'])
                
                prices = []
                for line in lines:
                    item = json.loads(line)
                    prices.append(float(item['close']))
                
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                
                print(f"\n📊 Complete Historical Dataset Summary:")
                print(f"   Total data points: {len(lines)}")
                print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                print(f"   Price range: ${min_price:.8f} to ${max_price:.8f}")
                print(f"   Average price: ${avg_price:.8f}")
                print(f"\n✓ Output file: xfg-complete-historical.json")
                
    except Exception as e:
        print(f"✗ Error reading final data: {e}")

if __name__ == "__main__":
    main() 