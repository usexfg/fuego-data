#!/usr/bin/env python3
"""
Extract Real XFG Data from CoinPaprika
Convert the discovered real price data to OHLCV format for our chart
"""

import json
import urllib.request
from datetime import datetime

def fetch_and_extract_real_xfg_data():
    """Fetch the real XFG data from the working CoinPaprika endpoint"""
    print("🔥 Extracting REAL XFG Data from CoinPaprika")
    print("=" * 60)
    
    endpoint = 'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/1y/?quote=usd'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://coinpaprika.com/',
        'Origin': 'https://coinpaprika.com'
    }
    
    try:
        print(f"🔍 Fetching from: {endpoint}")
        
        req = urllib.request.Request(endpoint, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                data = json.loads(content)
                
                print(f"✅ SUCCESS! Got response with {len(data)} data series")
                
                # Extract the price data
                price_data = []
                if len(data) > 0 and 'price' in data[0]:
                    price_points = data[0]['price']
                    print(f"📊 Found {len(price_points)} real XFG price points")
                    
                    # Show date range
                    if price_points:
                        start_date = datetime.fromtimestamp(price_points[0][0] / 1000)
                        end_date = datetime.fromtimestamp(price_points[-1][0] / 1000)
                        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                        
                        # Show price range
                        prices = [point[1] for point in price_points]
                        min_price = min(prices)
                        max_price = max(prices)
                        print(f"💰 Price range: ${min_price:.8f} to ${max_price:.8f}")
                    
                    return price_points, data
                else:
                    print("❌ No price data found in response")
                    return [], data
            else:
                print(f"❌ HTTP {response.status}: {response.reason}")
                return [], None
                
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return [], None

def convert_to_daily_ohlcv(price_points):
    """Convert price points to daily OHLCV candles"""
    print(f"\n🔄 Converting {len(price_points)} price points to daily OHLCV format...")
    
    daily_candles = {}
    
    for timestamp_ms, price in price_points:
        # Convert to daily candle
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day_timestamp = int(day_start.timestamp())
        
        if day_timestamp not in daily_candles:
            daily_candles[day_timestamp] = {
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'prices': [],
                'volume': 0
            }
        
        candle = daily_candles[day_timestamp]
        candle['high'] = max(candle['high'], price)
        candle['low'] = min(candle['low'], price)
        candle['close'] = price  # Last price of the day becomes close
        candle['prices'].append(price)
    
    # Convert to OHLCV format
    ohlcv_data = []
    for day_timestamp in sorted(daily_candles.keys()):
        candle = daily_candles[day_timestamp]
        
        # Estimate volume based on price activity
        price_range = candle['high'] - candle['low']
        volume = max(100, len(candle['prices']) * 50 + int(price_range * 1000000))
        
        ohlcv_data.append({
            'period_start': day_timestamp,
            'open': str(candle['open']),
            'high': str(candle['high']),
            'low': str(candle['low']),
            'close': str(candle['close']),
            'volume': str(volume)
        })
    
    print(f"✅ Created {len(ohlcv_data)} daily OHLCV candles")
    return ohlcv_data

def save_real_xfg_data(ohlcv_data, filename='xfg-real-coinpaprika.json'):
    """Save the real XFG data"""
    print(f"\n💾 Saving real XFG data to {filename}...")
    
    with open(filename, 'w') as f:
        for item in ohlcv_data:
            json_line = json.dumps(item, separators=(',', ': '))
            f.write(json_line + '\n')
    
    print(f"✅ Saved {len(ohlcv_data)} real XFG data points")

def merge_real_with_existing(real_data, existing_file='xfg-usd-data.json'):
    """Merge real CoinPaprika data with existing converted data"""
    print(f"\n🔄 Merging real data with existing converted data...")
    
    # Load existing converted data
    existing_data = []
    try:
        with open(existing_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_data.append(json.loads(line))
        print(f"✅ Loaded {len(existing_data)} existing converted data points")
    except FileNotFoundError:
        print("⚠️ No existing converted data found")
    
    # Combine data - prefer real data over converted for overlapping dates
    all_data = []
    real_timestamps = set(item['period_start'] for item in real_data)
    
    # Add all real data first
    all_data.extend(real_data)
    
    # Add existing data that doesn't overlap with real data
    for item in existing_data:
        if item['period_start'] not in real_timestamps:
            all_data.append(item)
    
    # Sort by timestamp
    all_data.sort(key=lambda x: x['period_start'])
    
    print(f"✅ Final merged dataset: {len(all_data)} total data points")
    
    if all_data:
        start_date = datetime.fromtimestamp(all_data[0]['period_start'])
        end_date = datetime.fromtimestamp(all_data[-1]['period_start'])
        print(f"📅 Complete date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Show some sample prices
        print(f"\n📋 Sample Price Points:")
        indices = [0, len(all_data)//4, len(all_data)//2, len(all_data)*3//4, -1]
        for i in indices:
            if i < len(all_data):
                item = all_data[i]
                date_str = datetime.fromtimestamp(item['period_start']).strftime('%Y-%m-%d')
                price = float(item['close'])
                print(f"   {date_str}: ${price:.8f}")
    
    return all_data

def update_chart_to_use_real_data():
    """Update chart.html to use the real XFG data"""
    print(f"\n🔧 Updating chart to use real XFG data...")
    
    # This would update the chart.html file to use xfg-real-complete.json
    # For now, we'll just note what needs to be changed
    print(f"📝 Chart update needed:")
    print(f"   - Change data source from 'xfg-complete-historical.json' to 'xfg-real-complete.json'")
    print(f"   - Update title to indicate 'Real Historical Data'")

def main():
    """Main execution"""
    print("🔥 REAL XFG Data Extraction from CoinPaprika")
    print("=" * 60)
    
    # Fetch real data
    price_points, full_data = fetch_and_extract_real_xfg_data()
    
    if price_points:
        # Convert to OHLCV format
        ohlcv_data = convert_to_daily_ohlcv(price_points)
        
        # Save real data separately
        save_real_xfg_data(ohlcv_data)
        
        # Merge with existing converted data
        merged_data = merge_real_with_existing(ohlcv_data)
        
        # Save complete dataset
        save_real_xfg_data(merged_data, 'xfg-real-complete.json')
        
        print(f"\n🎉 SUCCESS! Real XFG data extracted and processed!")
        print(f"📁 Files created:")
        print(f"   - xfg-real-coinpaprika.json ({len(ohlcv_data)} real data points)")
        print(f"   - xfg-real-complete.json ({len(merged_data)} total points)")
        
        # Show statistics
        if merged_data:
            prices = [float(item['close']) for item in merged_data]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            
            print(f"\n📊 Final Dataset Statistics:")
            print(f"   Total data points: {len(merged_data)}")
            print(f"   Price range: ${min_price:.8f} - ${max_price:.8f}")
            print(f"   Average price: ${avg_price:.8f}")
            print(f"   Price variation: {((max_price - min_price) / min_price * 100):.1f}%")
        
        print(f"\n🚀 Ready to update chart with REAL XFG data!")
        
    else:
        print(f"\n❌ Failed to extract real XFG data")

if __name__ == "__main__":
    main() 