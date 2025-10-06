"""Search service for tracklist and SoundCloud searches."""

import asyncio
from typing import Any

from whats_this_id.core.scraping.soundcloud import SoundCloudHandler
from whats_this_id.frontend.services.tracklist_manager_service import (
    get_tracklist_manager_service,
)


class SearchService:
    """Service for handling tracklist and SoundCloud searches."""

    _instance: "SearchService" | None = None
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

    @property
    def soundcloud_handler(self) -> SoundCloudHandler:
        """Get or create the SoundCloud handler (lazy initialization)."""
        if self._soundcloud_handler is None:
            self._soundcloud_handler = SoundCloudHandler()
        return self._soundcloud_handler

    async def search_tracklist_and_soundcloud(
        self, query_text: str, soundcloud_delay: float = 2.0
    ) -> tuple[Any, str]:
        """Run tracklist search and SoundCloud search concurrently with bounded delay.

        Args:
            query_text: The search query string
            soundcloud_delay: Delay in seconds before starting SoundCloud search to avoid rate limiting

        Returns:
            Tuple of (tracklist_result, dj_set_url)
        """
        # Start both searches concurrently
        loop = asyncio.get_running_loop()

        # Start tracklist search in a thread to avoid event loop conflicts
        # Use the event loop's default executor instead of creating a new one
        tracklist_future = loop.run_in_executor(
            None,  # Use default executor
            self.tracklist_manager_service.search_tracklist,
            query_text.strip(),
        )

        # Start SoundCloud search task with configurable delay
        soundcloud_task = asyncio.create_task(
            self.search_soundcloud(query_text, soundcloud_delay)
        )

        # Wait for both to complete
        tracklist_result, dj_set_url = await asyncio.gather(
            tracklist_future, soundcloud_task
        )

        # Extract the tracklist from the SearchRun
        final_tracklist = self.tracklist_manager_service.get_tracklist_from_search_run(
            tracklist_result
        )

        return final_tracklist, dj_set_url or ""

    def search_tracklist(self, query_text: str) -> Any:
        """Search for tracklist only (synchronous).

        Args:
            query_text: The search query string

        Returns:
            Tracklist search result
        """
        search_run = self.tracklist_manager_service.search_tracklist(query_text.strip())
        return self.tracklist_manager_service.get_tracklist_from_search_run(search_run)

    async def search_soundcloud(self, query_text: str, delay: float) -> str:
        """Run SoundCloud search with a bounded delay to respect rate limits.

        Args:
            query_text: The search query string
            delay: Delay in seconds before starting the search

        Returns:
            SoundCloud URL
        """
        # Apply bounded delay before starting the search
        await asyncio.sleep(delay)

        result = await self.soundcloud_handler.find_dj_set_url(query_text)
        return result or ""


def get_search_service() -> SearchService:
    """Get the singleton search service instance."""
    return SearchService()
