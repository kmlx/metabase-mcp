"""
Metabase FastMCP Server

A FastMCP server that provides tools to interact with Metabase databases,
execute queries, manage cards, and work with collections.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx
from mcp.server.fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import settings
from .logger import get_logger, setup_access_log_filter

# Use uvicorn's logger for everything
logger = get_logger("main")

# Setup access log filter to ignore ping requests
setup_access_log_filter()


class MetabaseClient:
    """Simple Metabase client that creates new HTTP connections per request"""

    def __init__(self) -> None:
        self.base_url = settings.METABASE_URL.rstrip("/")
        self.api_key = settings.METABASE_API_KEY

    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers"""
        return {"Content-Type": "application/json", "X-API-KEY": self.api_key}

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make authenticated request to Metabase API using a new client each time"""
        url = f"{self.base_url}/api{path}"
        headers = self._get_headers()

        logger.debug(f"Making {method} request to {path}")

        # Configure timeout for this request
        timeout_config = httpx.Timeout(
            connect=settings.HTTP_CONNECT_TIMEOUT,
            read=settings.HTTP_READ_TIMEOUT,
            write=settings.HTTP_CONNECT_TIMEOUT,
            pool=settings.HTTP_READ_TIMEOUT,
        )

        # Create a new client for each request with configurable settings
        async with httpx.AsyncClient(
            timeout=timeout_config,
            http2=settings.HTTP_ENABLE_HTTP2,
        ) as client:
            try:
                response = await client.request(method=method, url=url, headers=headers, **kwargs)

                if not response.is_success:
                    error_data = response.json() if response.content else {}
                    error_message = (
                        f"API request failed with status {response.status_code}: {response.text}"
                    )
                    logger.warning(f"{error_message} - {error_data}")
                    raise Exception(error_message)

                logger.debug(f"Successful response from {path}")
                return response.json()

            except httpx.ConnectTimeout as e:
                error_message = f"Connection timeout ({settings.HTTP_CONNECT_TIMEOUT}s) when connecting to {url}: {e}"
                logger.error(error_message)
                raise Exception(error_message)
            except httpx.ReadTimeout as e:
                error_message = f"Read timeout ({settings.HTTP_READ_TIMEOUT}s) when reading response from {url}: {e}"
                logger.error(error_message)
                raise Exception(error_message)
            except httpx.ConnectError as e:
                error_message = f"Connection error when connecting to {url}: {e}"
                logger.error(error_message)
                raise Exception(error_message)


@dataclass
class AppContext:
    """Type-safe application context for FastMCP lifespan."""

    metabase_client: MetabaseClient


@asynccontextmanager
async def app_lifespan(_: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    # Initialize once at app startup (not per request)
    logger.debug("app_lifespan: Initializing Mock Metabase client")
    metabase_client = MetabaseClient()
    try:
        yield AppContext(metabase_client=metabase_client)
    finally:
        # Mock cleanup - no actual resources to clean up
        logger.debug("app_lifespan: Mock cleanup complete")


# Initialize MCP server
mcp = FastMCP(
    settings.MCP_SERVER_NAME,
    lifespan=app_lifespan,
    stateless_http=True,
    log_level=settings.LOG_LEVEL,
    host=settings.HOST,
    port=settings.PORT,
)


# Add /ping endpoint using custom routes
@mcp.custom_route("/ping", methods=["GET"])
async def ping(_: Request) -> Response:
    """Simple ping endpoint for health checks"""
    return JSONResponse({"status": "ok", "timestamp": datetime.now().isoformat()})


# Tool implementations
@mcp.tool()
async def find_candidate_collections(
    ctx: Context, query: str, limit_collections: int = 10
) -> dict[str, Any]:
    """
    Find collections whose names contain the query words.
    Simple collection name matching - fast and reliable.

    Args:
        query: Text to search for in collection names.
        limit_collections: Max collections to return.
    """
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        # Get all collections
        collections = await metabase_client.request("GET", "/collection")

        if not isinstance(collections, list):
            return {
                "query": query,
                "collections": [],
                "results": {"total_collections_searched": 0, "matched_collections": 0},
            }

        # Search collection names
        search_term = query.strip().lower()
        matched_collections = []

        for collection in collections:
            if not collection:  # Skip None collections
                continue

            collection_name = (collection.get("name") or "").lower()
            collection_desc = (collection.get("description") or "").lower()

            # Check if query matches collection name or description
            if search_term in collection_name or search_term in collection_desc:
                matched_collections.append(
                    {
                        "collection_id": collection.get("id"),
                        "collection_name": collection.get("name"),
                        "description": collection.get("description"),
                        "parent_id": collection.get("parent_id"),
                        "archived": collection.get("archived", False),
                    }
                )

        # Sort by name and apply limit
        matched_collections.sort(key=lambda x: x.get("collection_name", "").lower())
        limited_collections = matched_collections[:limit_collections]

        return {
            "query": query,
            "collections": limited_collections,
            "results": {
                "total_collections_searched": len(collections),
                "matched_collections": len(matched_collections),
                "returned_collections": len(limited_collections),
            },
            "note": "Collections matching query in name or description. Use search_cards_in_collections next.",
        }

    except Exception as e:
        logger.error(f"Error finding candidate collections: {e}")
        raise


@mcp.tool()
async def search_cards_in_collections(
    ctx: Context, query: str, collection_ids: list[int], limit: int = 25, offset: int = 0
) -> dict[str, Any]:
    """
    Search for cards within specific collections by getting all cards from each collection
    and filtering by query in card names and descriptions.

    Args:
        query: Text to search for in card names and descriptions.
        collection_ids: List of collection IDs to search within.
        limit: Max cards to return (page size).
        offset: Number of matches to skip (pagination).
    """
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        search_term = query.strip().lower()
        all_matches = []

        # Get cards from each collection
        for collection_id in collection_ids:
            try:
                # Use existing list_cards_by_collection logic
                all_cards = await metabase_client.request("GET", "/card")

                if isinstance(all_cards, list):
                    # Filter by collection_id
                    collection_cards = [
                        card for card in all_cards if card.get("collection_id") == collection_id
                    ]

                    # Search within these cards
                    for card in collection_cards:
                        card_name = (card.get("name") or "").lower()
                        card_description = (card.get("description") or "").lower()

                        # Check if search term is in name or description
                        if search_term in card_name or search_term in card_description:
                            # Keep only essential fields
                            matched_card = {
                                "id": card.get("id"),
                                "name": card.get("name"),
                                "description": card.get("description"),
                                "collection_id": card.get("collection_id"),
                                "updated_at": card.get("updated_at"),
                                "created_at": card.get("created_at"),
                            }
                            all_matches.append(matched_card)

            except Exception as e:
                logger.warning(f"Error searching collection {collection_id}: {e}")
                continue

        # Sort by updated_at desc (most recent first)
        all_matches.sort(key=lambda x: x.get("updated_at") or "", reverse=True)

        total_found = len(all_matches)

        # Apply pagination
        paginated_matches = all_matches[offset : offset + limit]

        return {
            "query": query,
            "collections_searched": collection_ids,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(paginated_matches),
                "total_found": total_found,
                "has_more": offset + limit < total_found,
            },
            "cards": paginated_matches,
            "note": f"Searched {len(collection_ids)} collections for '{query}'. Found {total_found} matching cards.",
        }

    except Exception as e:
        logger.error(f"Error searching cards in collections: {e}")
        raise


@mcp.tool()
async def search_metabase(
    ctx: Context,
    query: str,
    limit: int = 20,
    models: list[str] | None = None,
    archived: bool = False,
    search_native_query: bool | None = None,
) -> dict[str, Any]:
    """
    Search for items in Metabase using the search API.

    Args:
        query: Search term to find in item names and descriptions
        limit: Maximum number of results to return (default: 20)
        models: List of item types to filter by (e.g., ["card", "dashboard", "collection"])
        archived: Include archived items in results (default: False)
        search_native_query: Search within native SQL queries (default: None)
    """
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        # Build base query parameters
        params = {"q": query, "limit": limit, "archived": str(archived).lower()}

        # Add optional parameters
        if search_native_query is True:
            params["search_native_query"] = "true"

        # Build query string to handle multiple models parameters
        if models is not None:
            params["models"] = models
        query_string = urlencode(params, doseq=True)
        result = await metabase_client.request("GET", f"/search?{query_string}")

        # Add search metadata to response
        search_info = {
            "query": query,
            "limit": limit,
            "models": models,
            "total_results": len(result.get("data", []) if isinstance(result, dict) else result),
        }

        if isinstance(result, dict):
            result["search_info"] = search_info
        else:
            result = {"data": result, "search_info": search_info}

        return result

    except Exception as e:
        logger.error(f"Error searching Metabase: {e}")
        raise


@mcp.tool()
async def list_databases(ctx: Context) -> Any:
    """List all databases in Metabase"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client
        result = await metabase_client.request("GET", "/database")
        return result
    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        raise


@mcp.tool()
async def list_cards(ctx: Context) -> Any:
    """List all questions/cards in Metabase (WARNING: Large dataset - 1700+ cards, may timeout)"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client
        result = await metabase_client.request("GET", "/card")
        return result
    except Exception as e:
        logger.error(f"Error listing cards: {e}")
        raise


@mcp.tool()
async def list_cards_paginated(
    ctx: Context, limit: int = 50, offset: int = 0, filter_type: str = "all"
) -> Any:
    """
    List cards with pagination and filtering to avoid timeout issues

    Args:
        limit: Maximum number of cards to return (default: 50)
        offset: Number of cards to skip (default: 0)
        filter_type: Filter type - 'all', 'mine', 'bookmarked', 'archived' (default: 'all')
    """
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        # Build query parameters
        params = {}
        if filter_type != "all":
            params["f"] = filter_type

        # Convert params to query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/card?{query_string}" if query_string else "/card"

        result = await metabase_client.request("GET", endpoint)

        # Apply pagination manually since Metabase API doesn't support limit/offset for cards
        if isinstance(result, list):
            paginated_result = result[offset : offset + limit]
            return {
                "cards": paginated_result,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "returned": len(paginated_result),
                    "total_available": len(result),
                    "has_more": offset + limit < len(result),
                },
                "filter": filter_type,
            }
        else:
            return result

    except Exception as e:
        logger.error(f"Error listing cards with pagination: {e}")
        raise


@mcp.tool()
async def list_cards_by_collection(ctx: Context, collection_id: int) -> Any:
    """
    List cards in a specific collection (smaller, focused dataset)

    Args:
        collection_id: ID of the collection to filter by
    """
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        # Get all cards first, then filter by collection
        # Note: Metabase API doesn't have direct collection filtering for cards
        result = await metabase_client.request("GET", "/card")

        if isinstance(result, list):
            # Filter by collection_id
            filtered_cards = [card for card in result if card.get("collection_id") == collection_id]

            return {
                "cards": filtered_cards,
                "collection_id": collection_id,
                "count": len(filtered_cards),
                "message": f"Found {len(filtered_cards)} cards in collection {collection_id}",
            }
        else:
            return result

    except Exception as e:
        logger.error(f"Error listing cards by collection {collection_id}: {e}")
        raise


@mcp.tool()
async def execute_card(ctx: Context, card_id: int, parameters: dict[str, Any] | None = None) -> Any:
    """Execute a Metabase question/card and get results"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        payload = {}
        if parameters:
            payload["parameters"] = parameters

        result = await metabase_client.request("POST", f"/card/{card_id}/query", json=payload)
        return result
    except Exception as e:
        logger.error(f"Error executing card {card_id}: {e}")
        raise


@mcp.tool()
async def execute_query(
    ctx: Context,
    database_id: int,
    query: str,
    native_parameters: list[dict[str, Any]] | None = None,
) -> Any:
    """Execute a SQL query against a Metabase database"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        payload = {"database": database_id, "type": "native", "native": {"query": query}}

        if native_parameters:
            payload["native"]["parameters"] = native_parameters  # type: ignore

        result = await metabase_client.request("POST", "/dataset", json=payload)
        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise


@mcp.tool()
async def create_card(
    ctx: Context,
    name: str,
    database_id: int,
    query: str,
    description: str | None = None,
    collection_id: int | None = None,
    visualization_settings: dict[str, Any] | None = None,
) -> Any:
    """Create a new question/card in Metabase"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        payload = {
            "name": name,
            "database_id": database_id,
            "dataset_query": {
                "database": database_id,
                "type": "native",
                "native": {"query": query},
            },
            "display": "table",
            "visualization_settings": visualization_settings or {},
        }

        if description:
            payload["description"] = description
        if collection_id is not None:
            payload["collection_id"] = collection_id

        result = await metabase_client.request("POST", "/card", json=payload)
        return result
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        raise


@mcp.tool()
async def list_collections(ctx: Context) -> Any:
    """List all collections in Metabase"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client
        result = await metabase_client.request("GET", "/collection")
        return result
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise


@mcp.tool()
async def create_collection(
    ctx: Context,
    name: str,
    description: str | None = None,
    color: str | None = None,
    parent_id: int | None = None,
) -> Any:
    """Create a new collection in Metabase"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        payload = {"name": name}

        if description:
            payload["description"] = description
        if color:
            payload["color"] = color
        if parent_id is not None:
            payload["parent_id"] = str(parent_id)

        result = await metabase_client.request("POST", "/collection", json=payload)
        return result
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise


@mcp.tool()
async def list_tables(ctx: Context, database_id: int) -> str:
    """List all tables in a database with formatted markdown output"""
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        result = await metabase_client.request("GET", f"/database/{database_id}/metadata")

        # Extract tables from the metadata response
        tables = result.get("tables", [])

        # Format tables with only the requested fields: table_id, display_name, description, entity_type
        formatted_tables = []
        for table in tables:
            table_info = {
                "table_id": table.get("id"),
                "display_name": table.get("display_name"),
                "description": table.get("description") or "No description",
                "entity_type": table.get("entity_type"),
            }
            formatted_tables.append(table_info)

        # Sort by display_name for better readability
        formatted_tables.sort(key=lambda x: x.get("display_name", ""))

        # Generate markdown output
        markdown_output = f"# Tables in Database {database_id}\n\n"
        markdown_output += f"**Total Tables:** {len(formatted_tables)}\n\n"

        if not formatted_tables:
            markdown_output += "*No tables found in this database.*\n"
            return markdown_output

        # Create markdown table
        markdown_output += "| Table ID | Display Name | Description | Entity Type |\n"
        markdown_output += "|----------|--------------|-------------|--------------|\n"

        for table in formatted_tables:
            table_id = table.get("table_id", "N/A")
            display_name = table.get("display_name", "N/A")
            description = table.get("description", "No description")
            entity_type = table.get("entity_type", "N/A")

            # Escape pipe characters in content to prevent table formatting issues
            description = description.replace("|", "\\|")
            display_name = display_name.replace("|", "\\|")

            markdown_output += f"| {table_id} | {display_name} | {description} | {entity_type} |\n"

        return markdown_output

    except Exception as e:
        logger.error(f"Error listing tables for database {database_id}: {e}")
        raise


@mcp.tool()
async def get_table_fields(ctx: Context, table_id: int, limit: int = 20) -> Any:
    """Get all fields/columns in a table

    Args:
        table_id: The ID of the table
        limit: Maximum number of fields to return (default: 20)
    """
    try:
        # Access type-safe lifespan context
        metabase_client = ctx.request_context.lifespan_context.metabase_client

        result = await metabase_client.request("GET", f"/table/{table_id}/query_metadata")

        # Apply field limiting if limit > 0 and there are more fields than the limit
        if limit > 0 and "fields" in result and len(result["fields"]) > limit:
            total_fields = len(result["fields"])
            result["fields"] = result["fields"][:limit]
            result["_truncated"] = True
            result["_total_fields"] = total_fields
            result["_limit_applied"] = limit

        return result
    except Exception as e:
        logger.error(f"Error getting table fields for table {table_id}: {e}")
        raise
