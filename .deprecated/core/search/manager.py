"""
Tracklist search manager that coordinates multiple search strategies.
"""

from .searcher import SearchResult
from .tracklist1001 import Tracklist1001SearchStrategy


class TracklistSearchManager:
    """Manages multiple search strategies for finding tracklists."""

    def __init__(self, search_config: dict = None):
        self.search_config = search_config or {}
        self._strategies = {"1001tracklists": Tracklist1001SearchStrategy()}

    def search(self, query: str) -> list[SearchResult]:
        """Search using all enabled strategies."""
        results = []

        for strategy_name, strategy in self._strategies.items():
            # Check if strategy is disabled in config
            if self.search_config.get(strategy_name, True) is False:
                continue

            try:
                strategy_results = strategy.search(query)
                results.extend(strategy_results)
            except Exception as e:
                raise e

        return results
