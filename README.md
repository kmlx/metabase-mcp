# Metabase FastMCP Server

A FastMCP (Model Context Protocol) server for Metabase, built with Python. This server provides tools to interact with Metabase databases, execute queries, manage cards, and work with collections.

## Features

- List and manage Metabase databases
- Execute SQL queries and saved questions/cards
- Create and manage cards (questions)
- Work with collections
- List tables and fields
- API Key authentication

## Installation

### Quick Start with uv (Recommended)

1. **Install uv** if not already installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup**:
```bash
git clone <repository-url>
cd metabase-mcp
uv sync  # Install dependencies and create virtual environment
```

3. **Configure environment**:
```bash
# Create .env file with your Metabase configuration
echo "METABASE_URL=http://localhost:3000" > .env
echo "METABASE_API_KEY=your-api-key-here" >> .env
```

## Configuration

Set the following environment variables in your `.env` file:

- `METABASE_URL`: Your Metabase instance URL
- `METABASE_API_KEY`: Your Metabase API key

## Usage

### Run the Server

```bash
# STDIO transport (default for MCP integration)
uv run server.py

# SSE transport (for web applications)
uv run server.py --sse

# HTTP transport
uv run server.py --http
```

### Claude Desktop Integration

To integrate with Claude Desktop, add the configuration to `~/Library/Application\ Support/Claude/claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "metabase-mcp": {
            "command": "uv",
            "args": ["run", "python", "/path/to/metabase-mcp-kmlx/server.py"],
            "cwd": "/path/to/metabase-mcp-kmlx"
        }
    }
}
```

## Available Tools

### Database & Schema Tools
- `list_databases`: List all databases in Metabase
- `list_tables`: List all tables in a database with formatted output
- `get_table_fields`: Get all fields/columns in a table

### Card & Query Tools
- `list_cards`: List all questions/cards in Metabase (WARNING: Large dataset)
- `list_cards_paginated`: List cards with pagination to avoid timeout issues
- `execute_card`: Execute a Metabase question/card and get results
- `execute_query`: Execute a SQL query against a Metabase database
- `create_card`: Create a new question/card in Metabase

### Collection Management Tools
- `list_collections`: List all collections in Metabase
- `list_cards_by_collection`: List cards in a specific collection (focused dataset)
- `create_collection`: Create a new collection in Metabase

### Smart Search Tools
- `search_metabase`: Universal search using Metabase search API (cards, dashboards, collections)
- `find_candidate_collections`: Find collections by name/description matching (fast)
- `search_cards_in_collections`: Search for cards within specific collections (targeted)

## Development

### Development Setup

```bash
# Install development dependencies (Python 3.12+)
uv sync --group dev

# Run tests
uv run pytest

# Format and lint code
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run black .               # Alternative formatter
uv run isort .               # Import sorting

# Type checking
uv run mypy server.py
```
