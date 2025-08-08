#!/usr/bin/env python3
"""
Test Collection Search Tools
Tests the new find_candidate_collections and search_cards_in_collections tools
with configurable test data for different Metabase instances.
"""

import asyncio
import time
import os
import json
from fastmcp import Client
from server import mcp

# Configurable test queries - customize for your Metabase instance
TEST_COLLECTION_QUERIES = [
    "Team", "Reports", "Dashboard", "Analytics", "Sales"
]

TEST_CARD_SEARCH_SCENARIOS = [
    {"query": "revenue", "description": "Revenue-related cards"},
    {"query": "user", "description": "User-related cards"}, 
    {"query": "total", "description": "Cards with totals/summaries"}
]

# Known collection IDs to test (update these for your instance)
# Set to None to auto-discover from collection search results
KNOWN_COLLECTION_IDS = None  # Example: [1, 2, 3, 10]

def parse_result(result, function_name):
    """Helper to parse MCP tool results consistently"""
    try:
        if result and len(result) > 0:
            first_item = result[0]
            if hasattr(first_item, 'text'):
                content_str = first_item.text
                if content_str.strip().startswith('{'):
                    data = json.loads(content_str)
                    return data, len(content_str)
        return None, 0
    except Exception as e:
        print(f"   ❌ Error parsing {function_name} result: {e}")
        return None, 0

async def test_collection_search_tools(client):
    """Test the new collection search MCP tools"""
    print("\n" + "🔍" * 80)
    print("COLLECTION SEARCH TOOLS TEST")
    print("🔍" * 80)
    
    results_summary = {}
    discovered_collections = []
    
    # 1. Test find_candidate_collections
    print("\n1️⃣ Testing find_candidate_collections...")
    
    for i, query in enumerate(TEST_COLLECTION_QUERIES):
        print(f"\n   🔎 Query {i+1}: '{query}'")
        start_time = time.time()
        
        try:
            result = await client.call_tool("find_candidate_collections", {
                "query": query,
                "limit_collections": 5
            })
            elapsed = time.time() - start_time
            
            collections_data, response_size = parse_result(result, "find_candidate_collections")
            if collections_data and 'collections' in collections_data:
                collections = collections_data['collections']
                results_info = collections_data.get('results', {})
                total_searched = results_info.get('total_collections_searched', 0)
                matched = results_info.get('matched_collections', 0)
                
                print(f"   ✅ {elapsed:.1f}s | {len(collections)} returned | {matched}/{total_searched} matches | {response_size:,} chars")
                
                # Store discovered collections for later use
                for collection in collections:
                    if collection and collection.get('collection_id'):
                        discovered_collections.append(collection.get('collection_id'))
                
                # Show collections found
                for j, collection in enumerate(collections):
                    if collection:
                        cname = collection.get('collection_name', 'Unknown')
                        cid = collection.get('collection_id', 'Unknown')
                        print(f"      📁 {j+1}. {cname} (ID: {cid})")
                        
                results_summary[f'find_candidate_collections_{query}'] = {
                    'time': elapsed, 
                    'collections': len(collections),
                    'total_matches': matched
                }
            else:
                print(f"   ⚠️  No collections found for '{query}'")
                results_summary[f'find_candidate_collections_{query}'] = {'time': elapsed, 'collections': 0}
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Query '{query}' failed after {elapsed:.1f}s: {e}")
            results_summary[f'find_candidate_collections_{query}'] = {'time': elapsed, 'error': str(e)}
    
    # Use discovered collections or fallback to known ones
    test_collection_ids = KNOWN_COLLECTION_IDS or list(set(discovered_collections[:6]))
    
    if not test_collection_ids:
        print("\n⚠️  No collection IDs available for card search testing")
        return results_summary
    
    # 2. Test search_cards_in_collections
    print(f"\n2️⃣ Testing search_cards_in_collections...")
    print(f"   Using collection IDs: {test_collection_ids[:3]}...")
    
    for i, scenario in enumerate(TEST_CARD_SEARCH_SCENARIOS):
        query = scenario["query"]
        description = scenario["description"]
        # Use a subset of collections to avoid too many API calls
        collection_ids = test_collection_ids[:3]
        
        print(f"\n   🎯 Scenario {i+1}: '{query}' - {description}")
        print(f"      Searching in collections: {collection_ids}")
        
        start_time = time.time()
        try:
            result = await client.call_tool("search_cards_in_collections", {
                "query": query,
                "collection_ids": collection_ids,
                "limit": 10,
                "offset": 0
            })
            elapsed = time.time() - start_time
            
            cards_data, response_size = parse_result(result, "search_cards_in_collections")
            if cards_data and 'cards' in cards_data:
                cards = cards_data['cards']
                pagination = cards_data.get('pagination', {})
                total_found = pagination.get('total_found', 0)
                returned = pagination.get('returned', 0)
                
                print(f"   ✅ {elapsed:.1f}s | {returned}/{total_found} cards found | {response_size:,} chars")
                
                # Show sample cards
                for j, card in enumerate(cards[:3]):
                    cname = card.get('name', 'Unknown')
                    cid = card.get('id', 'Unknown')
                    collection_id = card.get('collection_id', 'Unknown')
                    print(f"      📄 {j+1}. {cname} (ID: {cid}, Collection: {collection_id})")
                        
                results_summary[f'search_cards_in_collections_{i+1}'] = {
                    'time': elapsed, 
                    'total_found': total_found,
                    'returned': returned
                }
            else:
                print(f"   ⚠️  No cards found for '{query}'")
                results_summary[f'search_cards_in_collections_{i+1}'] = {'time': elapsed, 'cards': 0}
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Scenario {i+1} failed after {elapsed:.1f}s: {e}")
            results_summary[f'search_cards_in_collections_{i+1}'] = {'time': elapsed, 'error': str(e)}
    
    # Performance Summary
    print("\n" + "📊" * 80)
    print("COLLECTION SEARCH PERFORMANCE SUMMARY")
    print("📊" * 80)
    
    find_times = []
    search_times = []
    
    for func_name, result in results_summary.items():
        if 'find_candidate_collections' in func_name and 'error' not in result:
            find_times.append(result['time'])
        elif 'search_cards_in_collections' in func_name and 'error' not in result:
            search_times.append(result['time'])
            
        if 'error' in result:
            print(f"❌ {func_name:35} | FAILED: {result['error']}")
        else:
            time_taken = result['time']
            extra_info = ""
            if 'collections' in result:
                extra_info = f"{result['collections']} collections found"
            elif 'returned' in result:
                extra_info = f"{result['returned']} cards found"
            print(f"✅ {func_name:35} | {time_taken:5.1f}s | {extra_info}")
    
    # Summary statistics
    if find_times:
        avg_find = sum(find_times) / len(find_times)
        print(f"\n🎯 find_candidate_collections average: {avg_find:.1f}s ({len(find_times)} successful tests)")
        
    if search_times:
        avg_search = sum(search_times) / len(search_times)
        print(f"🎯 search_cards_in_collections average: {avg_search:.1f}s ({len(search_times)} successful tests)")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   • Use find_candidate_collections first to discover relevant collections")
    print(f"   • Then use search_cards_in_collections with specific collection IDs")
    print(f"   • Both tools are fast and return focused results")
    print(f"   • Perfect for building smart card discovery workflows")
    
    return results_summary

async def main():
    """Main test function"""
    print("🚀 Testing Metabase Collection Search Tools")
    print("=" * 80)
    
    # Check environment
    if not os.getenv("METABASE_URL"):
        print("⚠️  METABASE_URL not found in environment")
        print("   Make sure your .env file is configured with Metabase credentials")
        return False
        
    if not (os.getenv("METABASE_API_KEY") or 
            (os.getenv("METABASE_USER_EMAIL") and os.getenv("METABASE_PASSWORD"))):
        print("⚠️  No Metabase credentials found")
        print("   Configure METABASE_API_KEY or METABASE_USER_EMAIL/METABASE_PASSWORD")
        return False
    
    try:
        # Test with FastMCP client
        async with Client(mcp) as client:
            print("✅ Connected to MCP server")
            
            # Run collection search tests
            results = await test_collection_search_tools(client)
            
            # Summary
            total_tests = len(results)
            successful_tests = len([r for r in results.values() if 'error' not in r])
            
            print(f"\n🎯 TEST SUMMARY:")
            print(f"   Total tests: {total_tests}")
            print(f"   Successful: {successful_tests}")
            print(f"   Failed: {total_tests - successful_tests}")
            print(f"   Success rate: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "   No tests run")
            
            return successful_tests == total_tests
            
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        print("   Check your Metabase configuration and credentials")
        return False

if __name__ == "__main__":
    asyncio.run(main())