"""Simple logging using uvicorn's logger."""

import logging


class AccessLogFilter(logging.Filter):
    """Filter to exclude GET /ping requests from access logs."""

    def filter(self, record):
        # Filter out GET /ping requests from access logs
        if hasattr(record, "getMessage"):
            message = record.getMessage()
            if "GET /ping" in message:
                return False
        return True


def get_logger(name: str):
    """Get uvicorn's logger"""
    return logging.getLogger("uvicorn")


def setup_access_log_filter():
    """Setup access log filter to ignore ping requests."""
    access_logger = logging.getLogger("uvicorn.access")
    ping_filter = AccessLogFilter()
    access_logger.addFilter(ping_filter)
