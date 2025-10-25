"""Frontend wrapper for DJ set processor service with UI concerns."""

import streamlit as st
from dj_set_downloader import DomainTracklist, JobStatus, JobTracksInfoResponse

from whats_this_id.core.services.djset_processor import DJSetProcessorService
from whats_this_id.frontend.config import AppConfig


class FrontendDJSetProcessorService:
    """Frontend wrapper for DJ set processor service with UI error handling."""

    def __init__(self, base_url: str = AppConfig.DEFAULT_API_BASE_URL) -> None:
        self._service = DJSetProcessorService(base_url)

    def check_health(self) -> tuple[bool, str]:
        """Check if the DJ set processor service is healthy."""
        return self._service.check_health()

    def submit_processing_job(
        self,
        dj_set_url: str,
        tracklist: DomainTracklist,
        file_extension: str = AppConfig.DEFAULT_FILE_EXTENSION,
        max_concurrent_tasks: int = AppConfig.DEFAULT_MAX_CONCURRENT_TASKS,
    ) -> tuple[bool, str, str | None]:
        """Submit a DJ set processing job with UI error handling."""
        success, message, job_id = self._service.submit_processing_job(
            dj_set_url, tracklist, file_extension, max_concurrent_tasks
        )

        if not success:
            st.error(message)

        return success, message, job_id

    def get_job_status(self, job_id: str) -> JobStatus | None:
        """Get the status of a processing job with UI error handling."""
        try:
            return self._service.get_job_status(job_id)
        except Exception as e:
            st.error(f"Error checking job status: {e}")
            return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a processing job with UI error handling."""
        success = self._service.cancel_job(job_id)
        if not success:
            st.error("Error canceling job")
        return success

    def download_all_tracks(self, job_id: str) -> tuple[bytearray, str] | None:
        """Download all tracks as ZIP with UI error handling."""
        result = self._service.download_all_tracks(job_id)
        if result is None:
            st.error("Error downloading tracks")
        return result

    def download_single_track(
        self, job_id: str, track_number: int
    ) -> tuple[bytearray, str] | None:
        """Download a single track file with UI error handling."""
        result = self._service.download_single_track(
            job_id, track_number, AppConfig.DEFAULT_FILE_EXTENSION
        )
        if result is None:
            st.error(f"Error downloading track '{track_number}'")
        return result

    def get_tracks_info(self, job_id: str) -> JobTracksInfoResponse | None:
        """Get detailed track information with UI error handling."""
        result = self._service.get_tracks_info(job_id)
        if result is None:
            st.error("Error getting tracks info")
        return result

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Get MIME type for a file based on its extension."""
        return DJSetProcessorService.get_mime_type(filename)

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format."""
        return DJSetProcessorService.format_file_size(size_bytes)


# Global frontend service instance
djset_processor_service = FrontendDJSetProcessorService()


def display_api_error(message: str, show_service_hint: bool = True) -> None:
    """Display a consistent API error message.

    Args:
        message: Error message to display
        show_service_hint: Whether to show service connection hint
    """
    st.error(message)
    if show_service_hint:
        st.error(
            f"Make sure the DJ set processor service is running on {AppConfig.DEFAULT_API_BASE_URL}"
        )
