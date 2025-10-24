"""Search service for tracklist searches."""

from dj_set_downloader import DomainTracklist

from whats_this_id.frontend.services.tracklist_orchestrator import (
    tracklist_orchestrator_service,
)


class SearchService:
    """Service for handling tracklist searches."""

    def search_tracklist(self, query_text: str) -> tuple[DomainTracklist, str]:
        """Run tracklist search."""
        tracklist, url = tracklist_orchestrator_service.search_tracklist(query_text)

        return tracklist, url


search_service = SearchService()
