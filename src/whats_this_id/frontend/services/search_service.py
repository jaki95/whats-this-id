"""Search service for tracklist and SoundCloud searches."""

import asyncio
import concurrent.futures
from functools import partial
from typing import Any, Optional, Tuple

from whats_this_id.agents import TracklistSearchCrew
from whats_this_id.core.scraping.soundcloud import find_soundcloud_djset


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
            self._crew = None
            self._initialized = True

    @property
    def crew(self) -> TracklistSearchCrew:
        """Get or create the tracklist search crew (lazy initialization)."""
        if self._crew is None:
            self._crew = TracklistSearchCrew()
        return self._crew

    async def search_tracklist_and_soundcloud(self, query_text: str) -> Tuple[Any, str]:
        """Run tracklist search and SoundCloud search concurrently.

        Args:
            query_text: The search query string

        Returns:
            Tuple of (tracklist_result, dj_set_url)
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create partial functions for the searches
            tracklist_search = partial(
                lambda q: self.crew.crew().kickoff(inputs={"dj_set": q}),
                query_text.strip(),
            )
            soundcloud_search = partial(find_soundcloud_djset, query_text)

            # Submit both tasks to run concurrently
            loop = asyncio.get_event_loop()
            tracklist_future = loop.run_in_executor(executor, tracklist_search)
            soundcloud_future = loop.run_in_executor(executor, soundcloud_search)

            # Wait for both to complete
            tracklist_result, dj_set_url = await asyncio.gather(
                tracklist_future, soundcloud_future
            )

            return tracklist_result, dj_set_url

    def search_tracklist(self, query_text: str) -> Any:
        """Search for tracklist only (synchronous).

        Args:
            query_text: The search query string

        Returns:
            Tracklist search result
        """
        return self.crew.crew().kickoff(inputs={"dj_set": query_text.strip()})

    def search_soundcloud(self, query_text: str) -> str:
        """Search for SoundCloud DJ set URL (synchronous).

        Args:
            query_text: The search query string

        Returns:
            SoundCloud URL
        """
        return find_soundcloud_djset(query_text)


def get_search_service() -> SearchService:
    """Get the singleton search service instance."""
    return SearchService()
