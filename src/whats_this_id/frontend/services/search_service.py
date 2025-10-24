"""Search service for tracklist and SoundCloud searches."""

import asyncio
from typing import Optional

from dj_set_downloader import DomainTracklist

from whats_this_id.frontend.services.tracklist_manager_service import (
    get_tracklist_manager_service,
)


class SearchService:
    """Service for handling tracklist and SoundCloud searches."""

    _instance: Optional["SearchService"] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the search service (only once)."""
        if not self._initialized:
            self._tracklist_manager_service = None
            self._soundcloud_handler = None
            self._initialized = True

    @property
    def tracklist_manager_service(self):
        """Get or create the tracklist manager service (lazy initialization)."""
        if self._tracklist_manager_service is None:
            self._tracklist_manager_service = get_tracklist_manager_service()
        return self._tracklist_manager_service

    async def search_tracklist_and_soundcloud(self, query_text: str) -> DomainTracklist:
        """Run tracklist search and SoundCloud search concurrently with bounded delay."""
        # Start both searches concurrently
        loop = asyncio.get_running_loop()

        # Start tracklist search in a thread to avoid event loop conflicts
        # Use the event loop's default executor instead of creating a new one
        tracklist_future = loop.run_in_executor(
            None,  # Use default executor
            self.tracklist_manager_service.search_tracklist,
            query_text.strip(),
        )

        tracklist_result = await asyncio.gather(
            tracklist_future,
        )

        return tracklist_result[0][0], tracklist_result[0][1]


def get_search_service() -> SearchService:
    """Get the singleton search service instance."""
    return SearchService()
