# Metabase MCP Server

A FastMCP server for Metabase integration that provides tools to interact with Metabase databases, execute queries, manage cards (questions), and work with collections.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd metabase-mcp

# Install dependencies
uv sync
```

## Configuration

Set required environment variables in a `.env` file:

```bash
METABASE_URL=https://your-metabase-instance.com
METABASE_API_KEY=your-api-key-here

# Optional settings (defaults shown)
MCP_TRANSPORT=streamable-http  # or "stdio" for IDE integration
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO

# HTTP Client Configuration (optional)
HTTP_CONNECT_TIMEOUT=10.0      # Connection timeout in seconds (1.0-60.0)
HTTP_READ_TIMEOUT=30.0         # Read timeout in seconds (5.0-300.0)
HTTP_ENABLE_HTTP2=false        # Enable HTTP/2 support
```

## Running

```bash
# Default (HTTP transport)
uv run python -m src

# STDIO transport (for IDE integration)
MCP_TRANSPORT=stdio uv run python -m src
```

## Available Tools

### Database & Schema Tools
- **`list_databases`** - List all databases in Metabase
- **`list_tables(database_id)`** - List tables in a database with formatted markdown output
- **`get_table_fields(table_id, limit=20)`** - Get fields/columns in a table

### Card & Query Tools
- **`list_cards`** - List all questions/cards (WARNING: Large dataset, may timeout)
- **`list_cards_paginated(limit=50, offset=0, filter_type="all")`** - List cards with pagination
- **`list_cards_by_collection(collection_id)`** - List cards in a specific collection
- **`execute_card(card_id, parameters=None)`** - Execute a Metabase question/card
- **`execute_query(database_id, query, native_parameters=None)`** - Execute SQL query
- **`create_card(name, database_id, query, description=None, collection_id=None, visualization_settings=None)`** - Create new card

### Collection Management
- **`list_collections`** - List all collections
- **`create_collection(name, description=None, color=None, parent_id=None)`** - Create new collection

### Smart Search Tools
- **`search_metabase(query, limit=20, models=None, archived=False, search_native_query=None)`** - Search using Metabase API
- **`find_candidate_collections(query, limit_collections=10)`** - Find collections matching query
- **`search_cards_in_collections(query, collection_ids, limit=25, offset=0)`** - Search cards within specific collections

## Health Check

The server provides a `/ping` endpoint for health checks when running with HTTP transport.

## Integration

For Claude Desktop or Cursor IDE integration, set `MCP_TRANSPORT=stdio` in your environment.
