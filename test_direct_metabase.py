#!/usr/bin/env python3
"""
Test Metabase API directly to compare with MCP server results
"""

import requests
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()

METABASE_URL = os.getenv("METABASE_URL")
METABASE_API_KEY = os.getenv("METABASE_API_KEY")

def test_direct_metabase_api():
    """Test the Metabase API directly"""
    print("🔗 Testing Direct Metabase API")
    print("=" * 50)
    print(f"URL: {METABASE_URL}")
    print(f"API Key: {'✅ Set' if METABASE_API_KEY else '❌ Missing'}")
    print()
    
    if not METABASE_URL or not METABASE_API_KEY:
        print("❌ Missing Metabase configuration")
        return
    
    headers = {
        "X-API-KEY": METABASE_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Test different endpoints
    tests = [
        ("All cards", "/api/card"),
        ("Cards with ?f=all", "/api/card?f=all"),
        ("My cards only", "/api/card?f=mine"),
        ("Bookmarked cards", "/api/card?f=bookmarked"),
        ("Databases", "/api/database"),
        ("Collections", "/api/collection")
    ]
    
    results = {}
    
    for name, endpoint in tests:
        print(f"🚀 Testing {name}: {endpoint}")
        start_time = time.time()
        
        try:
            url = f"{METABASE_URL.rstrip('/')}{endpoint}"
            response = requests.get(url, headers=headers, timeout=30)
            elapsed = time.time() - start_time
            
            print(f"  Status: {response.status_code}")
            print(f"  Time: {elapsed:.1f}s")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"  📊 Count: {len(data)} items")
                        results[name] = len(data)
                        
                        # Show sample items
                        for i, item in enumerate(data[:2]):
                            if isinstance(item, dict):
                                item_name = item.get('name', 'Unknown')
                                item_id = item.get('id', 'N/A')
                                print(f"    - {item_name} (ID: {item_id})")
                    else:
                        print(f"  📊 Type: {type(data)}")
                        if isinstance(data, dict) and 'data' in data:
                            print(f"  📊 Data length: {len(data['data'])}")
                        
                except Exception as parse_error:
                    print(f"  ❌ Parse error: {parse_error}")
                    print(f"  Raw: {response.text[:200]}...")
                    
            else:
                print(f"  ❌ Error: {response.text[:200]}")
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ Request failed after {elapsed:.1f}s: {e}")
            
        print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 30)
    for name, count in results.items():
        print(f"{name}: {count} items")
    
    # Performance comparison
    if "All cards" in results:
        card_count = results["All cards"]
        print(f"\n🎯 Your Metabase has {card_count} total cards")
        
        if card_count > 1000:
            print("⚠️  Large dataset - this could cause timeouts in some clients")
        elif card_count > 500:
            print("⚠️  Medium dataset - might be slow in some clients")
        else:
            print("✅ Reasonable dataset size")

if __name__ == "__main__":
    test_direct_metabase_api()