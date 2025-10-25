"""Search service for tracklist discovery."""

from dj_set_downloader import DomainTracklist
from trackidnet.client import SearchResult

from whats_this_id.core.search.strategy import SearchStrategy
from whats_this_id.core.search.trackid import TrackIDNetSearchStrategy


class SearchService:
    """Service for managing search operations."""

    def __init__(self, strategy: SearchStrategy = TrackIDNetSearchStrategy()):
        self._strategy = strategy

    def search(self, query: str) -> list[SearchResult]:
        return self._strategy.search(query)

    def get_tracklist(self, url: str) -> tuple[DomainTracklist, str]:
        return self._strategy.get_tracklist(url)


# Global search service instance
search_service = SearchService()
