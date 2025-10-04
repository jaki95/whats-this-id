"""
Core module for tracklist search functionality.
"""

from .common import BaseOperation, ExecutionResult, SearchRun, StepLog

# Configuration
from .config import (
    BROWSER_CONFIG,
    CRAWLER_CONFIG,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    SEARCH_CONFIG,
)
from .fetchers.fetcher import Fetcher

# Main components
from .manager import TracklistManager
from .parsers.parser import Parser
from .search.searcher import Searcher

__all__ = [
    # Main components
    "TracklistManager",
    "Fetcher",
    "Parser",
    "Searcher",
    "SearchRun",
    "StepLog",
    "ExecutionResult",
    "BaseOperation",
    # Configuration
    "BROWSER_CONFIG",
    "CRAWLER_CONFIG",
    "SEARCH_CONFIG",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
]
