"""
Search strategies and result models.
"""

from abc import ABC, abstractmethod

from dj_set_downloader import DomainTracklist

from whats_this_id.core.search.models import SearchResult


class SearchStrategy(ABC):
    """Abstract base class for search strategies."""

    @abstractmethod
    def search(self, query: str) -> list[SearchResult]:
        """Search for tracklists using the given query."""
        pass

    def get_tracklist(self, url: str) -> DomainTracklist:
        """Get a tracklist from the given URL."""
        pass
