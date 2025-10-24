"""
Search strategies and result models.
"""

from abc import ABC, abstractmethod

from dj_set_downloader import DomainTracklist


class SearchResult:
    """Represents a single search result."""

    def __init__(self, link: str, title: str):
        self.link = link
        self.title = title


class SearchStrategy(ABC):
    """Abstract base class for search strategies."""

    @abstractmethod
    def search(self, query: str) -> list[SearchResult]:
        """Search for tracklists using the given query."""
        pass

    def get_tracklist(self, url: str) -> DomainTracklist:
        """Get a tracklist from the given URL."""
        pass
