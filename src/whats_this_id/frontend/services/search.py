"""Search service for tracklist searches."""

from dj_set_downloader import DomainTracklist

from whats_this_id.core.orchestration.orchestrator import Orchestrator


class SearchService:
    """Service for handling tracklist searches."""

    def __init__(self, orchestrator: Orchestrator = Orchestrator()):
        self.orchestrator = orchestrator

    def search_tracklist(self, query_text: str) -> list:
        """Run tracklist search."""
        return self.orchestrator.search_tracklist(query_text)
    
    def get_tracklist_for_result(self, search_result) -> tuple[DomainTracklist, str]:
        """Get full tracklist for a specific search result."""
        return self.orchestrator.get_tracklist_for_result(search_result)


search_service = SearchService()
