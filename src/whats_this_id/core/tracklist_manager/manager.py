"""
Unified manager that orchestrates all tracklist search operations.
"""

import logging
from typing import Any, Dict, Optional

from dj_set_downloader import DomainTracklist

from whats_this_id.core.search.trackid import TrackIDNetSearchStrategy

logger = logging.getLogger(__name__)


class TracklistManager:
    """Manager for tracklist search operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.searcher = TrackIDNetSearchStrategy()

    def run(self, query: str) -> tuple[DomainTracklist, str]:
        """Run a complete tracklist search operation."""
        results = self.searcher.search(query)
        if not results:
            raise ValueError("No results found")

        # TODO: Handle multiple results
        tracklist, url = self.searcher.get_tracklist(results[0].link)

        return tracklist, url
