# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastMCP (Model Context Protocol) server for Metabase integration. It provides tools to interact with Metabase databases, execute queries, manage cards (questions), and work with collections. The server supports multiple transport methods (STDIO, SSE, HTTP) and can be integrated with Claude Desktop, Cursor IDE, or used standalone.

## Architecture

### Core Components

- **`server.py`**: Main FastMCP server with all tool implementations
- **`MetabaseClient`**: HTTP client class handling Metabase API authentication and requests
- **Authentication**: Supports both API Key (preferred) and email/password session authentication
- **Transport Methods**: STDIO (default for IDE integration), SSE, HTTP

### Key Tool Categories

1. **Database & Schema Tools**: `list_databases`, `list_tables`, `get_table_fields`
2. **Card & Query Tools**: `list_cards*`, `execute_card`, `execute_query`, `create_card`
3. **Collection Management**: `list_collections`, `create_collection`, `list_cards_by_collection`
4. **Smart Search**: `search_metabase`, `find_candidate_collections`, `search_cards_in_collections`

### Authentication

The server uses API Key authentication with the `X-API-KEY` header.

## Development Commands

### Environment Setup
```bash
# Install dependencies and create virtual environment
uv sync

# Install development dependencies
uv sync --group dev
```

### Running the Server
```bash
# STDIO transport (default for IDE integration)
uv run python server.py

# SSE transport for web applications
uv run python server.py --sse

# HTTP transport
uv run python server.py --http

# Custom host/port via environment variables
HOST=localhost PORT=9000 uv run python server.py --sse
```

### Code Quality & Testing
```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Alternative formatters
uv run black .
uv run isort .

# Type checking
uv run mypy server.py

# Run tests
uv run pytest
```

## Configuration

### Environment Variables
Required in `.env` file:
- `METABASE_URL`: Metabase instance URL
- `METABASE_API_KEY`: Metabase API key

Optional:
- `HOST`: Server host (default: 0.0.0.0 for SSE/HTTP)
- `PORT`: Server port (default: 8000 for SSE/HTTP)

### Tool Configuration
- Line length: 100 characters (Black, Ruff, isort)
- Python version: 3.12+
- Import sorting: Black profile
- Type checking: Strict mode with mypy

## Common Development Patterns

### Adding New Tools
1. Use `@mcp.tool` decorator
2. Include proper type hints and docstrings
3. Handle errors with try/except and logger.error
4. Use `metabase_client.request()` for API calls
5. Return structured dict responses

### Error Handling
- Log errors with `logger.error()`
- Re-raise exceptions to propagate to MCP client
- Include context in error messages

### API Response Processing
- Check if response is list vs dict
- Apply pagination manually (Metabase API limitations)
- Include metadata in responses (counts, pagination info)

## Important Notes

- The `list_cards()` tool returns 1700+ cards and may timeout - use `list_cards_paginated()` instead
- Search tools are optimized: use `find_candidate_collections()` first, then `search_cards_in_collections()`
- SSE/HTTP transports require starting the server before IDE integration
- Uses per-request HTTP clients for automatic connection management