"""
Unified manager that orchestrates all tracklist search operations.
"""

import logging

from dj_set_downloader import DomainTracklist

from whats_this_id.core.search.models import SearchResult
from whats_this_id.core.search.strategy import SearchStrategy
from whats_this_id.core.search.trackid import TrackIDNetSearchStrategy

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrator for tracklist search operations."""

    def __init__(self, search_strategy: SearchStrategy = TrackIDNetSearchStrategy()):
        self.search_strategy = search_strategy

    def search_tracklist(self, query: str) -> list[SearchResult]:
        """Run a search operation and return search results metadata only."""
        search_results = self.search_strategy.search(query)
        if not search_results:
            raise ValueError("No results found")

        return search_results

    def get_tracklist_for_result(
        self, search_result: SearchResult
    ) -> tuple[DomainTracklist, str]:
        """Get the full tracklist for a specific search result."""
        return self.search_strategy.get_tracklist(search_result.link)
