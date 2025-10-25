"""Search service for tracklist discovery."""

from whats_this_id.core.search.strategy import SearchStrategy
from whats_this_id.core.search.trackid import TrackIDNetSearchStrategy


class SearchService:
    """Service for managing search operations."""
    
    def __init__(self, strategy: SearchStrategy = TrackIDNetSearchStrategy()):
        self._strategy = strategy


# Global search service instance
search_service = SearchService()
