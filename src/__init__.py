# MCP Server
from .config import settings
from .server import logger, mcp


def main() -> None:
    """Main function to start the MCP server."""
    try:
        logger.info(f"Starting MCP Server on {settings.HOST}:{settings.PORT}")

        # Use the standard FastMCP run method
        mcp.run(
            transport=settings.MCP_TRANSPORT,
        )

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise
