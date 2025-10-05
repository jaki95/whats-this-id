"""Service for the new tracklist search manager."""

from typing import Any, Optional

from whats_this_id.core.common import SearchRun
from whats_this_id.core.manager import TracklistManager


class TracklistManagerService:
    """Service for handling tracklist searches using the new manager."""

    _instance: Optional["TracklistManagerService"] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the tracklist manager service (only once)."""
        if not self._initialized:
            self._manager = TracklistManager()
            self._initialized = True

    @property
    def manager(self) -> TracklistManager:
        """Get the tracklist manager instance."""
        return self._manager

    def search_tracklist(self, query_text: str) -> SearchRun:
        """Search for tracklist using the new manager.

        Args:
            query_text: The search query string

        Returns:
            SearchRun result containing the tracklist and metadata
        """
        return self._manager.run(query_text.strip())

    def get_tracklist_from_search_run(self, search_run: SearchRun) -> Any:
        """Extract the tracklist from a SearchRun for frontend compatibility.

        Args:
            search_run: The SearchRun result from the manager

        Returns:
            DomainTracklist with frontend-compatible attributes or None if no results
        """
        if search_run.final_tracklist is not None:
            # Create a frontend-compatible tracklist by adding missing attributes
            tracklist = search_run.final_tracklist

            # Add frontend-expected attributes if they don't exist
            if not hasattr(tracklist, "name") or tracklist.name is None:
                tracklist.name = search_run.query
            if not hasattr(tracklist, "artist") or tracklist.artist is None:
                tracklist.artist = "Unknown Artist"
            if not hasattr(tracklist, "year") or tracklist.year is None:
                tracklist.year = 2024  # Default to current year as integer
            if not hasattr(tracklist, "genre") or tracklist.genre is None:
                tracklist.genre = "Electronic"

            return tracklist
        return None


def get_tracklist_manager_service() -> TracklistManagerService:
    """Get the singleton tracklist manager service instance."""
    return TracklistManagerService()
