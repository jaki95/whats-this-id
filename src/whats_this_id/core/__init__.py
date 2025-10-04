"""
Core module for tracklist search functionality.
"""

# Main components
from .manager import TracklistManager
from .common import SearchRun, StepLog, ExecutionResult, BaseOperation
from .fetchers.fetcher import Fetcher
from .parsers.parser import Parser
from .search.searcher import Searcher

# Configuration
from .config import (
    BROWSER_CONFIG,
    CRAWLER_CONFIG,
    SEARCH_CONFIG,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
)

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
