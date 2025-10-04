"""
Tracklist1001 search strategy implementation.
"""

import asyncio
from typing import List

from whats_this_id.core.scraping.google import GoogleHandler

from .searcher import SearchResult, SearchStrategy


class Tracklist1001SearchStrategy(SearchStrategy):
    """Search strategy for finding tracklists on 1001tracklists.com."""

    TARGET_SITE = "1001tracklists.com"

    def __init__(self):
        self.google_handler = GoogleHandler()

    def search(self, query: str) -> List[SearchResult]:
        """Search for tracklists on 1001tracklists.com."""
        try:
            # Run the async search in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._async_search(query))
            finally:
                loop.close()
            return result
        except Exception:
            return []

    async def _async_search(self, query: str) -> List[SearchResult]:
        """Internal async search method."""
        try:
            link = await self.google_handler.search_for_tracklist_link(
                self.TARGET_SITE, query
            )

            if link:
                return [
                    SearchResult(
                        url=link,
                        title=f"Tracklist: {query}",
                        snippet="Found tracklist on 1001tracklists.com",
                    )
                ]
            return []
        except Exception:
            return []
