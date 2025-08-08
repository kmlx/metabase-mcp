#!/usr/bin/env python3
"""
Comprehensive Metabase MCP Tools Test
Tests all major MCP tools with performance monitoring and safety checks.
Designed for public repo - no sensitive data.
"""

import asyncio
import time
import os
import json
from fastmcp import Client
from server import mcp

def parse_result(result, function_name):
    """Helper to parse MCP tool results consistently"""
    try:
        if result and len(result) > 0:
            first_item = result[0]
            if hasattr(first_item, 'text'):
                content_str = first_item.text
                if content_str.strip().startswith('['):
                    data = json.loads(content_str)
                    return data, len(content_str)
                elif content_str.strip().startswith('{'):
                    data = json.loads(content_str)
                    return data, len(content_str)
        return None, 0
    except Exception as e:
        print(f"   ❌ Error parsing {function_name} result: {e}")
        return None, 0

async def test_basic_tools(client):
    """Test basic database and collection tools"""
    print("\n" + "⚙️" * 80)
    print("BASIC TOOLS TEST")
    print("⚙️" * 80)
    
    results = {}
    
    # Test list_databases
    print("\n1️⃣ Testing list_databases...")
    start_time = time.time()
    try:
        db_result = await client.call_tool("list_databases", {})
        elapsed = time.time() - start_time
        
        db_data, response_size = parse_result(db_result, "list_databases")
        db_count = len(db_data) if isinstance(db_data, list) else 0
        print(f"✅ list_databases: {elapsed:.1f}s | {db_count} databases | {response_size:,} chars")
        results['list_databases'] = {'time': elapsed, 'count': db_count}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_databases failed after {elapsed:.1f}s: {e}")
        results['list_databases'] = {'time': elapsed, 'error': str(e)}
    
    # Test list_collections
    print("\n2️⃣ Testing list_collections...")
    start_time = time.time()
    try:
        collections_result = await client.call_tool("list_collections", {})
        elapsed = time.time() - start_time
        
        collections_data, response_size = parse_result(collections_result, "list_collections")
        collections_count = len(collections_data) if isinstance(collections_data, list) else 0
        print(f"✅ list_collections: {elapsed:.1f}s | {collections_count} collections | {response_size:,} chars")
        results['list_collections'] = {'time': elapsed, 'count': collections_count}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_collections failed after {elapsed:.1f}s: {e}")
        results['list_collections'] = {'time': elapsed, 'error': str(e)}
    
    return results

async def test_card_tools(client):
    """Test card-related tools with safety limits"""
    print("\n" + "🃏" * 80)
    print("CARD TOOLS TEST (WITH SAFETY LIMITS)")
    print("🃏" * 80)
    
    results = {}
    
    # Test list_cards_paginated (safe with small limit)
    print("\n1️⃣ Testing list_cards_paginated (limit=20)...")
    start_time = time.time()
    try:
        paginated_result = await client.call_tool("list_cards_paginated", {
            "limit": 20, 
            "offset": 0
        })
        elapsed = time.time() - start_time
        
        cards_data, response_size = parse_result(paginated_result, "list_cards_paginated")
        if cards_data and 'cards' in cards_data:
            count = len(cards_data['cards'])
            pagination_info = cards_data.get('pagination', {})
            total = pagination_info.get('total_available', 'Unknown')
            print(f"✅ list_cards_paginated: {elapsed:.1f}s | {count} cards returned | {total} total | {response_size:,} chars")
            results['list_cards_paginated'] = {'time': elapsed, 'count': count, 'total': total}
        else:
            print(f"⚠️  Unexpected response format")
            results['list_cards_paginated'] = {'time': elapsed, 'error': 'Unexpected format'}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_cards_paginated failed after {elapsed:.1f}s: {e}")
        results['list_cards_paginated'] = {'time': elapsed, 'error': str(e)}
    
    # Test list_cards_by_collection (pick first collection)
    print("\n2️⃣ Testing list_cards_by_collection...")
    try:
        # Get collections first to pick one
        collections_result = await client.call_tool("list_collections", {})
        collections_data, _ = parse_result(collections_result, "list_collections")
        
        if collections_data and isinstance(collections_data, list) and len(collections_data) > 0:
            # Find a non-empty collection (skip root/null)
            test_collection = None
            for collection in collections_data:
                if collection and collection.get('id') and collection.get('id') != 1:
                    test_collection = collection
                    break
            
            if test_collection:
                collection_id = test_collection['id']
                collection_name = test_collection.get('name', 'Unknown')
                print(f"   Testing with collection: {collection_name} (ID: {collection_id})")
                
                start_time = time.time()
                collection_result = await client.call_tool("list_cards_by_collection", {
                    "collection_id": collection_id
                })
                elapsed = time.time() - start_time
                
                cards_data, response_size = parse_result(collection_result, "list_cards_by_collection")
                if cards_data and 'cards' in cards_data:
                    count = cards_data.get('count', len(cards_data.get('cards', [])))
                    print(f"✅ list_cards_by_collection: {elapsed:.1f}s | {count} cards | {response_size:,} chars")
                    results['list_cards_by_collection'] = {'time': elapsed, 'count': count}
                else:
                    print(f"⚠️  No cards found in collection {collection_id}")
                    results['list_cards_by_collection'] = {'time': elapsed, 'count': 0}
            else:
                print("⚠️  No suitable collection found for testing")
                results['list_cards_by_collection'] = {'error': 'No test collection'}
        else:
            print("⚠️  Could not retrieve collections for testing")
            results['list_cards_by_collection'] = {'error': 'No collections available'}
            
    except Exception as e:
        print(f"❌ list_cards_by_collection setup failed: {e}")
        results['list_cards_by_collection'] = {'error': str(e)}
    
    return results

async def test_new_search_tools(client):
    """Test the new collection search tools"""
    print("\n" + "🔍" * 80)
    print("NEW SEARCH TOOLS TEST")
    print("🔍" * 80)
    
    results = {}
    
    # Test find_candidate_collections
    print("\n1️⃣ Testing find_candidate_collections...")
    test_queries = ["Team", "Report", "Dashboard", "Sales", "Data"]
    
    find_results = []
    for query in test_queries:
        start_time = time.time()
        try:
            result = await client.call_tool("find_candidate_collections", {
                "query": query,
                "limit_collections": 3
            })
            elapsed = time.time() - start_time
            
            collections_data, response_size = parse_result(result, "find_candidate_collections")
            if collections_data and 'collections' in collections_data:
                collections_found = len(collections_data['collections'])
                results_info = collections_data.get('results', {})
                total_matches = results_info.get('matched_collections', 0)
                
                print(f"   '{query}': {elapsed:.1f}s | {collections_found} collections | {total_matches} total matches")
                find_results.append({'query': query, 'time': elapsed, 'found': collections_found})
            else:
                print(f"   '{query}': {elapsed:.1f}s | No collections found")
                find_results.append({'query': query, 'time': elapsed, 'found': 0})
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   '{query}': FAILED after {elapsed:.1f}s - {e}")
            find_results.append({'query': query, 'time': elapsed, 'error': str(e)})
    
    avg_time = sum(r['time'] for r in find_results) / len(find_results)
    successful_queries = len([r for r in find_results if 'error' not in r])
    print(f"✅ find_candidate_collections: {avg_time:.1f}s average | {successful_queries}/{len(find_results)} successful")
    results['find_candidate_collections'] = {
        'average_time': avg_time, 
        'successful': successful_queries,
        'total': len(find_results)
    }
    
    # Test search_cards_in_collections
    print("\n2️⃣ Testing search_cards_in_collections...")
    
    # Use first few collections from any successful find query
    test_collection_ids = []
    for find_result in find_results:
        if 'error' not in find_result and find_result['found'] > 0:
            # Re-run the successful query to get collection IDs
            try:
                result = await client.call_tool("find_candidate_collections", {
                    "query": find_result['query'],
                    "limit_collections": 2
                })
                collections_data, _ = parse_result(result, "find_candidate_collections")
                if collections_data and 'collections' in collections_data:
                    for collection in collections_data['collections']:
                        if collection and collection.get('collection_id'):
                            test_collection_ids.append(collection['collection_id'])
                if len(test_collection_ids) >= 3:  # Limit to 3 collections
                    break
            except:
                continue
    
    if test_collection_ids:
        search_queries = ["user", "total", "report"]
        search_results = []
        
        for query in search_queries[:2]:  # Test only 2 queries to be safe
            start_time = time.time()
            try:
                result = await client.call_tool("search_cards_in_collections", {
                    "query": query,
                    "collection_ids": test_collection_ids[:2],  # Use max 2 collections
                    "limit": 5,
                    "offset": 0
                })
                elapsed = time.time() - start_time
                
                cards_data, response_size = parse_result(result, "search_cards_in_collections")
                if cards_data and 'cards' in cards_data:
                    cards_found = len(cards_data['cards'])
                    pagination = cards_data.get('pagination', {})
                    total_found = pagination.get('total_found', 0)
                    
                    print(f"   '{query}': {elapsed:.1f}s | {cards_found}/{total_found} cards found")
                    search_results.append({'query': query, 'time': elapsed, 'cards': cards_found})
                else:
                    print(f"   '{query}': {elapsed:.1f}s | No cards found")
                    search_results.append({'query': query, 'time': elapsed, 'cards': 0})
                    
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"   '{query}': FAILED after {elapsed:.1f}s - {e}")
                search_results.append({'query': query, 'time': elapsed, 'error': str(e)})
        
        if search_results:
            avg_search_time = sum(r['time'] for r in search_results) / len(search_results)
            successful_searches = len([r for r in search_results if 'error' not in r])
            print(f"✅ search_cards_in_collections: {avg_search_time:.1f}s average | {successful_searches}/{len(search_results)} successful")
            results['search_cards_in_collections'] = {
                'average_time': avg_search_time,
                'successful': successful_searches, 
                'total': len(search_results)
            }
    else:
        print("⚠️  No collection IDs available for card search testing")
        results['search_cards_in_collections'] = {'error': 'No test collections'}
    
    return results

async def main():
    """Main comprehensive test function"""
    print("🚀 Comprehensive Metabase MCP Tools Test")
    print("=" * 80)
    
    # Environment check
    if not os.getenv("METABASE_URL"):
        print("⚠️  METABASE_URL environment variable required")
        print("   Set up your .env file with Metabase configuration")
        return False
        
    if not (os.getenv("METABASE_API_KEY") or 
            (os.getenv("METABASE_USER_EMAIL") and os.getenv("METABASE_PASSWORD"))):
        print("⚠️  Metabase authentication required")
        print("   Set METABASE_API_KEY or METABASE_USER_EMAIL + METABASE_PASSWORD")
        return False
    
    total_start_time = time.time()
    
    try:
        async with Client(mcp) as client:
            print("✅ Connected to MCP server")
            
            # List available tools
            tools = await client.list_tools()
            print(f"📋 Found {len(tools)} available tools")
            
            # Run test suites
            basic_results = await test_basic_tools(client)
            card_results = await test_card_tools(client)
            search_results = await test_new_search_tools(client)
            
            # Overall summary
            total_elapsed = time.time() - total_start_time
            
            print("\n" + "🎯" * 80)
            print("COMPREHENSIVE TEST SUMMARY")
            print("🎯" * 80)
            
            all_results = {**basic_results, **card_results, **search_results}
            
            successful_tests = 0
            total_tests = 0
            
            for category, results in [("Basic Tools", basic_results), 
                                    ("Card Tools", card_results), 
                                    ("Search Tools", search_results)]:
                print(f"\n📊 {category}:")
                for tool_name, result in results.items():
                    total_tests += 1
                    if 'error' not in result:
                        successful_tests += 1
                        if 'time' in result:
                            print(f"   ✅ {tool_name}: {result['time']:.1f}s")
                        else:
                            print(f"   ✅ {tool_name}: OK")
                    else:
                        print(f"   ❌ {tool_name}: {result['error']}")
            
            success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            
            print(f"\n🏆 FINAL RESULTS:")
            print(f"   Total runtime: {total_elapsed:.1f}s")
            print(f"   Tests run: {total_tests}")
            print(f"   Successful: {successful_tests}")
            print(f"   Failed: {total_tests - successful_tests}")
            print(f"   Success rate: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print(f"   🎉 EXCELLENT: All major tools working well!")
            elif success_rate >= 60:
                print(f"   ✅ GOOD: Most tools working, check failed ones")
            else:
                print(f"   ⚠️  NEEDS ATTENTION: Several tools failing")
            
            return success_rate >= 60
            
    except Exception as e:
        print(f"❌ Failed to connect or run tests: {e}")
        print("   Check your Metabase configuration and server status")
        return False

if __name__ == "__main__":
    asyncio.run(main())