#!/usr/bin/env python3
"""
Inspect CoinPaprika XFG Data Response
Debug what data is actually available from CoinPaprika for XFG
"""

import json
import urllib.request
import urllib.error
from datetime import datetime

def inspect_coinpaprika_xfg():
    """Inspect all working CoinPaprika XFG endpoints"""
    print("🔍 Inspecting CoinPaprika XFG Data")
    print("=" * 60)
    
    coin_id = "xfg-fango"
    
    # Working endpoints based on previous test
    endpoints = [
        f'https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/latest',
        f'https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/today', 
        f'https://api.coinpaprika.com/v1/coins/{coin_id}',
        'https://graphsv2.coinpaprika.com/currency/data/xfg-fango/1y/?quote=usd'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://coinpaprika.com/',
        'Origin': 'https://coinpaprika.com'
    }
    
    for endpoint in endpoints:
        print(f"\n🔍 ENDPOINT: {endpoint}")
        print("-" * 80)
        
        try:
            req = urllib.request.Request(endpoint, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    data = json.loads(content)
                    
                    print(f"✅ SUCCESS!")
                    print(f"📊 Response Type: {type(data)}")
                    
                    if isinstance(data, list):
                        print(f"📋 Array Length: {len(data)}")
                        if len(data) > 0:
                            print(f"📄 First Item Type: {type(data[0])}")
                            print(f"📄 First Item:")
                            print(json.dumps(data[0], indent=2))
                            
                            if len(data) > 1:
                                print(f"📄 Last Item:")
                                print(json.dumps(data[-1], indent=2))
                                
                    elif isinstance(data, dict):
                        print(f"📄 Response Keys: {list(data.keys())}")
                        print(f"📄 Full Response:")
                        print(json.dumps(data, indent=2))
                        
                    print("\n" + "="*40)
                    
                else:
                    print(f"❌ HTTP {response.status}: {response.reason}")
                    
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")

def check_xfg_market_status():
    """Check if XFG has any trading markets"""
    print(f"\n🏪 Checking XFG Market Status")
    print("=" * 60)
    
    endpoints = [
        'https://api.coinpaprika.com/v1/coins/xfg-fango/markets',
        'https://api.coinpaprika.com/v1/coins/xfg-fango/events',
        'https://api.coinpaprika.com/v1/exchanges'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    for endpoint in endpoints:
        print(f"\n🔍 {endpoint}")
        try:
            req = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    if 'markets' in endpoint:
                        print(f"📊 XFG Markets: {len(data) if isinstance(data, list) else 'Not a list'}")
                        if isinstance(data, list) and len(data) > 0:
                            print("📋 Available Markets:")
                            for market in data[:5]:  # Show first 5
                                exchange = market.get('exchange_name', 'Unknown')
                                pair = market.get('pair', 'Unknown')
                                print(f"   - {exchange}: {pair}")
                        else:
                            print("❌ No active markets found for XFG")
                            
                    elif 'events' in endpoint:
                        print(f"📅 Events: {len(data) if isinstance(data, list) else 'Not a list'}")
                        
                    elif 'exchanges' in endpoint and isinstance(data, list):
                        # Check which exchanges might list XFG
                        xfg_exchanges = []
                        for exchange in data:
                            if exchange.get('active', False):
                                # This is a very basic check - we'd need to query each exchange
                                xfg_exchanges.append(exchange['name'])
                        print(f"🏪 Total Active Exchanges: {len([e for e in data if e.get('active', False)])}")
                        
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main inspection"""
    inspect_coinpaprika_xfg()
    check_xfg_market_status()
    
    print(f"\n💡 ANALYSIS:")
    print(f"   - XFG appears to have very limited trading data")
    print(f"   - CoinPaprika may not have historical price data for XFG")
    print(f"   - The coin exists in their database but lacks market activity")
    print(f"   - This explains why we only get empty or minimal responses")

if __name__ == "__main__":
    main() 