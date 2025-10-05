"""Search service for tracklist and SoundCloud searches."""

import asyncio
import concurrent.futures
from typing import Any, Optional, Tuple

from whats_this_id.core.scraping.soundcloud import SoundCloudHandler
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

    @property
    def soundcloud_handler(self) -> SoundCloudHandler:
        """Get or create the SoundCloud handler (lazy initialization)."""
        if self._soundcloud_handler is None:
            self._soundcloud_handler = SoundCloudHandler()
        return self._soundcloud_handler

    async def search_tracklist_and_soundcloud(self, query_text: str) -> Tuple[Any, str]:
        """Run tracklist search and SoundCloud search with delay to avoid rate limiting.

        Args:
            query_text: The search query string

        Returns:
            Tuple of (tracklist_result, dj_set_url)
        """
        # Run tracklist search in a thread to avoid event loop conflicts
        with concurrent.futures.ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            tracklist_future = loop.run_in_executor(
                executor,
                self.tracklist_manager_service.search_tracklist,
                query_text.strip(),
            )

            # Wait for tracklist search to complete
            tracklist_result = await tracklist_future

        # Add a small delay to avoid rate limiting
        await asyncio.sleep(2)

        # Then run SoundCloud search
        dj_set_url = await self.soundcloud_handler.find_dj_set_url(query_text)

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

    async def search_soundcloud(self, query_text: str) -> str:
        """Search for SoundCloud DJ set URL (asynchronous).

        Args:
            query_text: The search query string

        Returns:
            SoundCloud URL
        """
        result = await self.soundcloud_handler.find_dj_set_url(query_text)
        return result or ""


def get_search_service() -> SearchService:
    """Get the singleton search service instance."""
    return SearchService()
