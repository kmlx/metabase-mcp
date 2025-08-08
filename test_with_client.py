#!/usr/bin/env python3
"""
Test Metabase MCP Server using FastMCP Client
This is the proper way to test MCP servers according to FastMCP documentation
"""

import asyncio
import time
import os
from fastmcp import Client
from server import mcp
import json

def parse_card_result(result, function_name):
    """Helper function to parse card results consistently"""
    try:
        if result and len(result) > 0:
            first_item = result[0]
            if hasattr(first_item, 'text'):
                content_str = first_item.text
                if content_str.strip().startswith('['):
                    cards_data = json.loads(content_str)
                    return cards_data, len(content_str)
                elif content_str.strip().startswith('{'):
                    card_data = json.loads(content_str)
                    return card_data, len(content_str)
        return None, 0
    except Exception as e:
        print(f"   ❌ Error parsing {function_name} result: {e}")
        return None, 0

async def test_all_card_functions(client):
    """Test all card-related MCP tools"""
    print("\n" + "🃏" * 60)
    print("COMPREHENSIVE CARD FUNCTIONS TEST")
    print("🃏" * 60)
    
    results_summary = {}
    
    # 1. Test list_cards_summary (should be fastest)
    print("\n1️⃣ Testing list_cards_summary (lightweight)...")
    start_time = time.time()
    try:
        summary_result = await client.call_tool("list_cards_summary", {})
        elapsed = time.time() - start_time
        
        cards_data, response_size = parse_card_result(summary_result, "list_cards_summary")
        if cards_data:
            total_count = cards_data.get('total_count', len(cards_data.get('cards_summary', [])))
            print(f"✅ list_cards_summary: {elapsed:.1f}s | {total_count} cards | {response_size:,} chars")
            print(f"   📊 Sample cards:")
            for i, card in enumerate(cards_data.get('cards_summary', [])[:3]):
                print(f"      • {card.get('name', 'Unknown')} (ID: {card.get('id')})")
        results_summary['list_cards_summary'] = {'time': elapsed, 'count': total_count if cards_data else 0}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_cards_summary failed after {elapsed:.1f}s: {e}")
        results_summary['list_cards_summary'] = {'time': elapsed, 'error': str(e)}
    
    # 2. Test list_my_cards (should be super fast - 0 results)
    print("\n2️⃣ Testing list_my_cards (user-owned only)...")
    start_time = time.time()
    try:
        my_cards_result = await client.call_tool("list_my_cards", {})
        elapsed = time.time() - start_time
        
        cards_data, response_size = parse_card_result(my_cards_result, "list_my_cards")
        count = len(cards_data) if isinstance(cards_data, list) else 0
        print(f"✅ list_my_cards: {elapsed:.1f}s | {count} cards | {response_size:,} chars")
        if count > 0:
            print(f"   📊 Your cards:")
            for i, card in enumerate(cards_data[:3]):
                print(f"      • {card.get('name', 'Unknown')} (ID: {card.get('id')})")
        else:
            print(f"   📊 No cards owned by current user (expected)")
        results_summary['list_my_cards'] = {'time': elapsed, 'count': count}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_my_cards failed after {elapsed:.1f}s: {e}")
        results_summary['list_my_cards'] = {'time': elapsed, 'error': str(e)}
    
    # 3. Test list_cards_paginated with small limit
    print("\n3️⃣ Testing list_cards_paginated (first 20 cards)...")
    start_time = time.time()
    try:
        paginated_result = await client.call_tool("list_cards_paginated", {"limit": 20, "offset": 0})
        elapsed = time.time() - start_time
        
        cards_data, response_size = parse_card_result(paginated_result, "list_cards_paginated")
        if cards_data and 'cards' in cards_data:
            count = len(cards_data['cards'])
            pagination_info = cards_data.get('pagination', {})
            print(f"✅ list_cards_paginated: {elapsed:.1f}s | {count} cards | {response_size:,} chars")
            print(f"   📊 Pagination: {pagination_info.get('offset', 0)}-{pagination_info.get('offset', 0) + count} of {pagination_info.get('total_available', '?')}")
            print(f"   📊 Sample cards:")
            for i, card in enumerate(cards_data['cards'][:3]):
                print(f"      • {card.get('name', 'Unknown')} (ID: {card.get('id')})")
        results_summary['list_cards_paginated'] = {'time': elapsed, 'count': count if cards_data else 0}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_cards_paginated failed after {elapsed:.1f}s: {e}")
        results_summary['list_cards_paginated'] = {'time': elapsed, 'error': str(e)}
    
    # 4. Test list_cards_by_collection (using collection 239 "Affiliates")
    print("\n4️⃣ Testing list_cards_by_collection (Affiliates - ID 239)...")
    start_time = time.time()
    try:
        collection_result = await client.call_tool("list_cards_by_collection", {"collection_id": 239})
        elapsed = time.time() - start_time
        
        cards_data, response_size = parse_card_result(collection_result, "list_cards_by_collection")
        if cards_data and 'cards' in cards_data:
            count = cards_data.get('count', len(cards_data['cards']))
            print(f"✅ list_cards_by_collection: {elapsed:.1f}s | {count} cards | {response_size:,} chars")
            print(f"   📊 Collection 239 cards:")
            for i, card in enumerate(cards_data['cards'][:3]):
                print(f"      • {card.get('name', 'Unknown')} (ID: {card.get('id')})")
        results_summary['list_cards_by_collection'] = {'time': elapsed, 'count': count if cards_data else 0}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_cards_by_collection failed after {elapsed:.1f}s: {e}")
        results_summary['list_cards_by_collection'] = {'time': elapsed, 'error': str(e)}
    
    # 5. Test original list_cards (may timeout - test last)
    print("\n5️⃣ Testing list_cards (original - WARNING: may timeout)...")
    print("⏰ This is the problematic function with 1732 cards...")
    start_time = time.time()
    try:
        original_result = await client.call_tool("list_cards", {})
        elapsed = time.time() - start_time
        
        cards_data, response_size = parse_card_result(original_result, "list_cards")
        count = len(cards_data) if isinstance(cards_data, list) else 0
        print(f"✅ list_cards: {elapsed:.1f}s | {count} cards | {response_size:,} chars")
        print(f"   📊 First few cards:")
        for i, card in enumerate(cards_data[:3] if cards_data else []):
            print(f"      • {card.get('name', 'Unknown')} (ID: {card.get('id')})")
        results_summary['list_cards'] = {'time': elapsed, 'count': count}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ list_cards failed after {elapsed:.1f}s: {e}")
        if elapsed > 25:
            print("🎯 CONFIRMED: Original list_cards timeout issue!")
        results_summary['list_cards'] = {'time': elapsed, 'error': str(e)}
    
    # Performance Summary
    print("\n" + "📊" * 60)
    print("PERFORMANCE SUMMARY")
    print("📊" * 60)
    
    for func_name, result in results_summary.items():
        if 'error' in result:
            print(f"❌ {func_name:25} | FAILED after {result['time']:.1f}s | {result['error']}")
        else:
            count = result.get('count', 0)
            time_taken = result['time']
            print(f"✅ {func_name:25} | {time_taken:5.1f}s | {count:4d} cards")
    
    print(f"\n🎯 RECOMMENDATIONS FOR LIBRECHAT:")
    print(f"   • Use 'list_cards_summary' for browsing all cards")
    print(f"   • Use 'list_cards_paginated' with limit=50 for exploring")  
    print(f"   • Use 'list_cards_by_collection' for specific areas")
    print(f"   • Avoid 'list_cards' in LibreChat (too large)")

async def test_list_cards():
    """Test the list_cards endpoint that's timing out"""
    print("🚀 Testing Metabase MCP Server with FastMCP Client")
    print("=" * 60)
    
    try:
        # Create client connection to the MCP server
        async with Client(mcp) as client:
            print("✅ Connected to MCP server")
            
            # List available tools first
            print("\nStep 1: Listing available tools...")
            tools = await client.list_tools()
            print(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test list_databases (should be fast)
            print("\nStep 2: Testing list_databases...")
            start_time = time.time()
            try:
                db_result = await client.call_tool("list_databases", {})
                elapsed = time.time() - start_time
                print(f"✅ list_databases completed in {elapsed:.1f}s")
                if hasattr(db_result, 'content') and db_result.content:
                    print(f"Response length: {len(str(db_result.content))} chars")
                    print(f"Preview: {str(db_result.content)[:200]}...")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ list_databases failed after {elapsed:.1f}s: {e}")
            
            # Test all card-related functions
            await test_all_card_functions(client)
            
            # Test list_collections
            print("\nStep 4: Testing list_collections...")
            start_time = time.time()
            try:
                collections_result = await client.call_tool("list_collections", {})
                elapsed = time.time() - start_time
                print(f"✅ list_collections completed in {elapsed:.1f}s")
                if hasattr(collections_result, 'content') and collections_result.content:
                    print(f"Response length: {len(str(collections_result.content))} chars")
                    print(f"Preview: {str(collections_result.content)[:200]}...")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ list_collections failed after {elapsed:.1f}s: {e}")
                
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        print("Make sure your .env file is configured with valid Metabase credentials")
        return False
        
    print("\n" + "=" * 60)
    print("🎯 Test completed!")
    print("This test bypasses HTTP transport issues and tests directly")
    return True

async def main():
    """Main test function"""
    # Check environment variables
    if not os.getenv("METABASE_URL"):
        print("⚠️  No METABASE_URL found in environment")
        print("Make sure your .env file is configured")
        
    if not os.getenv("METABASE_API_KEY") and not (os.getenv("METABASE_USER_EMAIL") and os.getenv("METABASE_PASSWORD")):
        print("⚠️  No Metabase credentials found")
        print("Configure METABASE_API_KEY or METABASE_USER_EMAIL/METABASE_PASSWORD in .env")
    
    await test_list_cards()

if __name__ == "__main__":
    asyncio.run(main())