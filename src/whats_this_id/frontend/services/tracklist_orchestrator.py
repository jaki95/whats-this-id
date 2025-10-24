"""Service for the new tracklist search manager."""

from dj_set_downloader.models.domain_tracklist import DomainTracklist

from whats_this_id.core.orchestration.orchestrator import Orchestrator


class TracklistOrchestratorService:
    """Service for handling tracklist searches."""

    _orchestrator: Orchestrator = Orchestrator()

    def search_tracklist(self, query_text: str) -> tuple[DomainTracklist, str]:
        """Search for tracklist."""
        return self._orchestrator.run(query_text.strip())


tracklist_orchestrator_service = TracklistOrchestratorService()
