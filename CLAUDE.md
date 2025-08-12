# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastMCP (Model Context Protocol) server for Metabase integration. It provides tools to interact with Metabase databases, execute queries, manage cards (questions), and work with collections. The server supports multiple transport methods (STDIO, SSE, HTTP) and can be integrated with Claude Desktop, Cursor IDE, or used standalone.

## Architecture

### Core Components

- **`src/server.py`**: Main FastMCP server with all tool implementations using `mcp.server.fastmcp`
- **`src/config.py`**: Type-safe configuration management using pydantic-settings
- **`MetabaseClient`**: HTTP client class handling Metabase API authentication and requests
- **Authentication**: API Key authentication with `X-API-KEY` header
- **Transport Methods**: HTTP (default), STDIO (for IDE integration)

### Key Tool Categories

1. **Database & Schema Tools**: `list_databases`, `list_tables`, `get_table_fields`
2. **Card & Query Tools**: `list_cards*`, `execute_card`, `execute_query`, `create_card`
3. **Collection Management**: `list_collections`, `create_collection`, `list_cards_by_collection`
4. **Smart Search**: `search_metabase`, `find_candidate_collections`, `search_cards_in_collections`

### Configuration Management

The server uses `config.py` with pydantic-settings for type-safe configuration:
- Automatic `.env` file loading
- Environment variable validation
- Type-safe access to all settings
- Centralized configuration management

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
# Default transport (streamable-http)
uv run python -m src

# STDIO transport (for IDE integration)
MCP_TRANSPORT=stdio uv run python -m src

# Custom host/port via environment variables
HOST=localhost PORT=9000 uv run python -m src
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
uv run mypy src/

# Run tests
uv run pytest
```

## Configuration

Configuration is managed through `config.py` using pydantic-settings. All settings can be configured via environment variables or a `.env` file.

### Environment Variables
**Required:**
- `METABASE_URL`: Metabase instance URL
- `METABASE_API_KEY`: Metabase API key

**Optional (with defaults):**
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8080)
- `MCP_TRANSPORT`: Transport method - "streamable-http" or "stdio" (default: "streamable-http")
- `LOG_LEVEL`: Logging level (default: "INFO")
- `MCP_SERVER_NAME`: Server name (default: "metabase-mcp")

**HTTP Client Configuration:**
- `HTTP_CONNECT_TIMEOUT`: Connection timeout in seconds (default: 10.0, range: 1.0-60.0)
- `HTTP_READ_TIMEOUT`: Read timeout in seconds (default: 30.0, range: 5.0-300.0)
- `HTTP_ENABLE_HTTP2`: Enable HTTP/2 support for better performance (default: False)

### Tool Configuration
- Line length: 100 characters (Black, Ruff, isort)
- Python version: 3.12+
- Import sorting: Black profile
- Type checking: Strict mode with mypy

## Common Development Patterns

### Adding New Tools
1. Use `@mcp.tool()` decorator
2. Add `ctx: Context` as first parameter to access lifespan context
3. Include proper type hints and docstrings
4. Access MetabaseClient via `ctx.request_context.lifespan_context.metabase_client`
5. Handle errors with try/except and logger.error
6. Return structured responses

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
- Server uses `mcp.server.fastmcp` with type-safe context management
- Configuration uses pydantic-settings for validation and type safety
- Default transport is `streamable-http` - set `MCP_TRANSPORT=stdio` for IDE integration
- Uses per-request HTTP clients for automatic connection management
- Custom `/ping` endpoint available for health checks