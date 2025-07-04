#!/usr/bin/env python3
"""
Real XFG Data Fetcher from CoinPaprika
Fetches actual XFG historical data using the correct API endpoints
"""

import json
import urllib.request
import urllib.error
import time
from datetime import datetime, timedelta

def fetch_real_xfg_data():
    """Fetch real XFG data from CoinPaprika API using correct endpoints"""
    print("🔥 Fetching REAL XFG Data from CoinPaprika")
    print("=" * 60)
    
    # According to CoinPaprika docs, XFG API ID is "xfg-fango"
    coin_id = "xfg-fango"
    
    # Try multiple CoinPaprika endpoints for XFG data
    endpoints = [
        f'https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/latest',
        f'https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/historical?start=2018-01-01&end=2025-12-31',
        f'https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/today',
        f'https://api.coinpaprika.com/v1/coins/{coin_id}',
        f'https://graphs.coinpaprika.com/currency/data/{coin_id}/1y/?quote=usd',
        f'https://graphs.coinpaprika.com/currency/data/{coin_id}/max/?quote=usd',
        'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/max/?quote=usd',
        'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/1y/?quote=usd',
        'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/2y/?quote=usd'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://coinpaprika.com/',
        'Origin': 'https://coinpaprika.com'
    }
    
    all_data = []
    
    for endpoint in endpoints:
        try:
            print(f"\n🔍 Trying: {endpoint}")
            
            req = urllib.request.Request(endpoint, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    content = response.read()
                    
                    # Handle gzip encoding
                    if response.info().get('Content-Encoding') == 'gzip':
                        import gzip
                        content = gzip.decompress(content)
                    
                    data = json.loads(content.decode('utf-8'))
                    
                    print(f"✅ SUCCESS! Response type: {type(data)}")
                    
                    if isinstance(data, list) and len(data) > 0:
                        # OHLCV format from API
                        print(f"📊 Found {len(data)} OHLCV data points")
                        
                        for item in data:
                            if 'time_open' in item and 'close' in item:
                                try:
                                    timestamp = item['time_open']
                                    if isinstance(timestamp, str):
                                        # Parse ISO timestamp
                                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                        unix_timestamp = int(dt.timestamp())
                                    else:
                                        unix_timestamp = int(timestamp)
                                    
                                    all_data.append({
                                        'period_start': unix_timestamp,
                                        'open': str(item.get('open', 0)),
                                        'high': str(item.get('high', 0)),
                                        'low': str(item.get('low', 0)),
                                        'close': str(item.get('close', 0)),
                                        'volume': str(item.get('volume', 0))
                                    })
                                except Exception as e:
                                    print(f"⚠️ Error parsing item: {e}")
                                    continue
                        
                        print(f"✅ Processed {len(all_data)} valid data points")
                        
                    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'price' in data[0]:
                        # Graph format from graphsv2
                        prices = data[0].get('price', [])
                        print(f"📈 Found {len(prices)} price points")
                        
                        # Convert price data to OHLCV format
                        daily_candles = {}
                        for timestamp, price in prices:
                            # Convert to daily candles
                            dt = datetime.fromtimestamp(timestamp / 1000)
                            day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                            day_timestamp = int(day_start.timestamp())
                            
                            if day_timestamp not in daily_candles:
                                daily_candles[day_timestamp] = {
                                    'open': price,
                                    'high': price,
                                    'low': price,
                                    'close': price,
                                    'volume': 0,
                                    'prices': []
                                }
                            
                            candle = daily_candles[day_timestamp]
                            candle['high'] = max(candle['high'], price)
                            candle['low'] = min(candle['low'], price)
                            candle['close'] = price  # Last price becomes close
                            candle['prices'].append(price)
                        
                        # Convert to final format
                        for day_timestamp, candle in daily_candles.items():
                            all_data.append({
                                'period_start': day_timestamp,
                                'open': str(candle['open']),
                                'high': str(candle['high']),
                                'low': str(candle['low']),
                                'close': str(candle['close']),
                                'volume': str(len(candle['prices']) * 100)  # Estimated volume
                            })
                        
                        print(f"✅ Converted to {len(daily_candles)} daily candles")
                        
                    elif isinstance(data, dict):
                        # Single coin info
                        print(f"ℹ️ Coin info received: {data.get('name', 'Unknown')}")
                        if 'quotes' in data and 'USD' in data['quotes']:
                            price = data['quotes']['USD'].get('price', 0)
                            if price > 0:
                                timestamp = int(datetime.now().timestamp())
                                all_data.append({
                                    'period_start': timestamp,
                                    'open': str(price),
                                    'high': str(price),
                                    'low': str(price),
                                    'close': str(price),
                                    'volume': '100'
                                })
                                print(f"✅ Added current price: ${price}")
                    
                    # If we got good data, we can break or continue for more
                    if len(all_data) > 10:  # If we have substantial data
                        print(f"🎯 Got substantial data ({len(all_data)} points), continuing...")
                        
                else:
                    print(f"❌ HTTP {response.status}: {response.reason}")
                    
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
            if e.code == 403:
                print("   → API access forbidden")
            elif e.code == 404:
                print("   → Endpoint not found")
            elif e.code == 429:
                print("   → Rate limited, waiting...")
                time.sleep(5)
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            continue
    
    # Remove duplicates and sort
    if all_data:
        seen_timestamps = set()
        unique_data = []
        for item in all_data:
            timestamp = item['period_start']
            if timestamp not in seen_timestamps:
                seen_timestamps.add(timestamp)
                unique_data.append(item)
        
        unique_data.sort(key=lambda x: x['period_start'])
        
        print(f"\n🎉 FINAL RESULT:")
        print(f"   Total unique data points: {len(unique_data)}")
        
        if unique_data:
            start_date = datetime.fromtimestamp(unique_data[0]['period_start'])
            end_date = datetime.fromtimestamp(unique_data[-1]['period_start'])
            print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Show sample prices
            print(f"\n📋 Sample Real XFG Prices:")
            for i in [0, len(unique_data)//4, len(unique_data)//2, len(unique_data)*3//4, -1]:
                if i < len(unique_data):
                    item = unique_data[i]
                    date_str = datetime.fromtimestamp(item['period_start']).strftime('%Y-%m-%d')
                    price = float(item['close'])
                    print(f"   {date_str}: ${price:.8f}")
        
        return unique_data
    
    print("\n❌ No real XFG data could be fetched from any endpoint")
    return []

def save_real_xfg_data(data, filename='xfg-real-data.json'):
    """Save real XFG data"""
    if not data:
        print("❌ No data to save")
        return False
        
    print(f"\n💾 Saving real XFG data to {filename}...")
    
    with open(filename, 'w') as f:
        for item in data:
            json_line = json.dumps(item, separators=(',', ': '))
            f.write(json_line + '\n')
    
    print(f"✅ Saved {len(data)} real XFG data points")
    return True

def merge_with_converted_data(real_data, converted_file='xfg-usd-data.json'):
    """Merge real data with our converted XFG/BTC data"""
    print(f"\n🔄 Merging real data with converted XFG/BTC data...")
    
    # Load converted data
    converted_data = []
    try:
        with open(converted_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    converted_data.append(json.loads(line))
        print(f"✅ Loaded {len(converted_data)} converted XFG/BTC data points")
    except FileNotFoundError:
        print("⚠️ No converted data file found")
    
    # Combine all data
    all_data = converted_data + real_data
    
    # Remove duplicates by timestamp (prefer real data over converted)
    seen_timestamps = set()
    merged_data = []
    
    # First pass: add real data
    for item in real_data:
        timestamp = item['period_start']
        if timestamp not in seen_timestamps:
            seen_timestamps.add(timestamp)
            merged_data.append(item)
    
    # Second pass: add converted data that doesn't conflict
    for item in converted_data:
        timestamp = item['period_start']
        if timestamp not in seen_timestamps:
            seen_timestamps.add(timestamp)
            merged_data.append(item)
    
    # Sort by timestamp
    merged_data.sort(key=lambda x: x['period_start'])
    
    print(f"✅ Merged dataset: {len(merged_data)} total data points")
    
    if merged_data:
        start_date = datetime.fromtimestamp(merged_data[0]['period_start'])
        end_date = datetime.fromtimestamp(merged_data[-1]['period_start'])
        print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    return merged_data

def main():
    """Main execution"""
    print("🔥 REAL XFG Data Fetcher from CoinPaprika")
    print("Using correct API ID: xfg-fango")
    print("=" * 60)
    
    # Fetch real XFG data
    real_data = fetch_real_xfg_data()
    
    if real_data:
        # Save real data
        save_real_xfg_data(real_data)
        
        # Merge with existing converted data
        merged_data = merge_with_converted_data(real_data)
        
        # Save final merged dataset
        if merged_data:
            save_real_xfg_data(merged_data, 'xfg-real-complete.json')
            
            print(f"\n🎯 SUCCESS! Files created:")
            print(f"   - xfg-real-data.json (Real CoinPaprika data)")
            print(f"   - xfg-real-complete.json (Real + Converted data)")
            print(f"\n🚀 Ready to update chart with REAL XFG data!")
    else:
        print(f"\n❌ Could not fetch real XFG data from CoinPaprika")
        print(f"   This might be because:")
        print(f"   - XFG has limited trading history")
        print(f"   - Data is not available in CoinPaprika's free tier")
        print(f"   - API endpoints have changed")

if __name__ == "__main__":
    main() 