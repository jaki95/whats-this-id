"""
Unified manager that orchestrates all tracklist search operations.
"""

import logging

from dj_set_downloader import DomainTracklist

from whats_this_id.core.search.strategy import SearchStrategy
from whats_this_id.core.search.trackid import TrackIDNetSearchStrategy

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrator for tracklist search operations."""

    def __init__(self, search_strategy: SearchStrategy = TrackIDNetSearchStrategy()):
        self.search_strategy = search_strategy

    def run(self, query: str) -> tuple[DomainTracklist, str]:
        """Run a complete tracklist search operation."""
        search_results = self.search_strategy.search(query)
        if not search_results:
            raise ValueError("No results found")

        # TODO: Handle multiple results
        tracklist, url = self.search_strategy.get_tracklist(search_results[0].link)

        return tracklist, url
