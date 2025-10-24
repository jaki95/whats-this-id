"""Service for the new tracklist search manager."""

from typing import Optional

from dj_set_downloader.models.domain_tracklist import DomainTracklist

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

    def search_tracklist(self, query_text: str) -> tuple[DomainTracklist, str]:
        """Search for tracklist."""
        return self._manager.run(query_text.strip())


def get_tracklist_manager_service() -> TracklistManagerService:
    """Get the singleton tracklist manager service instance."""
    return TracklistManagerService()
