"""API service for DJ set processor backend."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Optional

import streamlit as st
from dj_set_downloader import (
    ApiClient,
    Configuration,
    DomainTracklist,
    DownloadsApi,
    JobRequest,
    JobsApi,
    JobStatus,
    JobTracksInfoResponse,
    ProcessApi,
    SystemApi,
)

from whats_this_id.frontend.config import AppConfig

# Constants for ZIP file validation
ZIP_SIGNATURE_1 = b"PK\x03\x04"  # Standard ZIP file signature
ZIP_SIGNATURE_2 = b"PK\x05\x06"  # Empty ZIP file signature
MIN_ZIP_SIZE = 4  # Minimum bytes needed to validate ZIP signature


class DJSetProcessorService:
    """Service for managing DJ set processor API operations."""

    _instance: DJSetProcessorService | None = None
    _initialized: bool = False

    def __new__(cls) -> DJSetProcessorService:
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_url: str = AppConfig.DEFAULT_API_BASE_URL) -> None:
        """Initialize the API service with configuration (only once).

        Args:
            base_url: Base URL for the DJ set processor API
        """
        if not self._initialized:
            config = Configuration(host=base_url)
            self.api_client = ApiClient(configuration=config)
            self.system_api = SystemApi(self.api_client)
            self.process_api = ProcessApi(self.api_client)
            self.jobs_api = JobsApi(self.api_client)
            self.downloads_api = DownloadsApi(self.api_client)
            self._initialized = True

    def check_health(self) -> tuple[bool, str]:
        """Check if the DJ set processor service is healthy.

        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            health = self.system_api.health_get()
            if health.status in ["healthy", "ok"]:
                return True, f"Service is healthy: {health.status}"
            else:
                return False, f"Service unhealthy: {health.status}"
        except Exception as e:
            return False, f"Failed to connect to service: {e}"

    def submit_processing_job(
        self,
        dj_set_url: str,
        tracklist: DomainTracklist,
        file_extension: str = AppConfig.DEFAULT_FILE_EXTENSION,
        max_concurrent_tasks: int = AppConfig.DEFAULT_MAX_CONCURRENT_TASKS,
    ) -> tuple[bool, str, str | None]:
        """Submit a DJ set processing job.

        Args:
            dj_set_url: URL of the DJ set to process
            tracklist: Tracklist data for the DJ set
            file_extension: File extension for downloaded tracks
            max_concurrent_tasks: Maximum number of concurrent download tasks

        Returns:
            Tuple of (success, message, job_id)
        """
        try:
            response = self.process_api.api_process_post_with_http_info(
                request=JobRequest(
                    url=dj_set_url,
                    tracklist=tracklist,
                    file_extension=file_extension,
                    max_concurrent_tasks=max_concurrent_tasks,
                )
            )
            if response.status_code != HTTPStatus.OK:
                error_msg = f"Error submitting processing job: {response.status_code}"
                st.error(error_msg)
                return False, error_msg, None

            return True, "Job submitted successfully", response.data.job_id
        except Exception as e:
            error_msg = f"Error submitting processing job: {e}"
            return False, error_msg, None

    def get_job_status(self, job_id: str) -> JobStatus | None:
        """Get the status of a processing job.

        Args:
            job_id: ID of the job to check

        Returns:
            JobStatus object if successful, None if failed

        Raises:
            Exception: If there's an error checking job status
        """
        try:
            response = self.jobs_api.api_jobs_id_get_with_http_info(job_id)
            if response.status_code != HTTPStatus.OK:
                st.error(f"Error checking job status: {response.status_code}")
                return None
            return response.data
        except Exception as e:
            raise Exception(f"Error checking job status: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a processing job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.jobs_api.api_jobs_id_cancel_post_with_http_info(job_id)
            if response.status_code != HTTPStatus.OK:
                st.error(f"Error canceling job: {response.status_code}")
                return False
            return True
        except Exception as e:
            st.error(f"Error canceling job: {e}")
            return False

    def download_all_tracks(self, job_id: str) -> Optional[tuple[bytearray, str]]:
        """Download all tracks as ZIP with proper error handling.

        Args:
            job_id: The processing job ID

        Returns:
            Tuple of (file_data, filename) if successful, None if failed
        """
        try:
            response = self.downloads_api.api_jobs_id_download_get_with_http_info(
                job_id
            )
            if response.status_code != HTTPStatus.OK:
                st.error(f"Error downloading tracks: {response.status_code}")
                return None

            filename = "tracks.zip"

            if not self._is_valid_zip_file(response.data):
                st.error("Downloaded file is not a valid ZIP file")
                return None

            return response.data, filename

        except Exception as e:
            st.error(f"Error downloading tracks: {e}")
            return None

    def download_single_track(
        self, job_id: str, track_number: int
    ) -> tuple[bytearray, str] | None:
        """Download a single track file.

        Args:
            job_id: The processing job ID
            track_number: Number of the track to download

        Returns:
            Tuple of (file_data, filename) if successful, None if failed
        """
        try:
            response = self.downloads_api.api_jobs_id_tracks_track_number_download_get_with_http_info(
                job_id, track_number
            )
            if response.status_code != HTTPStatus.OK:
                st.error(
                    f"Error downloading track '{track_number}': {response.status_code}"
                )
                return None

            filename = f"track_{track_number}.{AppConfig.DEFAULT_FILE_EXTENSION}"
            return response.data, filename

        except Exception as e:
            st.error(f"Error downloading track '{track_number}': {e}")
            return None

    def get_tracks_info(self, job_id: str) -> JobTracksInfoResponse | None:
        """Get detailed track information for a completed job.

        Args:
            job_id: The processing job ID

        Returns:
            JobTracksInfoResponse object if successful, None if failed
        """
        try:
            response = self.downloads_api.api_jobs_id_tracks_get_with_http_info(job_id)
            if response.status_code != HTTPStatus.OK:
                st.error(f"Error getting tracks info: {response.status_code}")
                return None
            return response.data
        except Exception as e:
            st.error(f"Error getting tracks info: {e}")
            return None

    def _is_valid_zip_file(self, file_data: bytes | bytearray | None) -> bool:
        """Validate if the given data represents a valid ZIP file.

        Args:
            file_data: The file data to validate

        Returns:
            True if valid ZIP file, False otherwise
        """
        if not file_data or len(file_data) < MIN_ZIP_SIZE:
            return False

        return file_data[:4] == ZIP_SIGNATURE_1 or file_data[:4] == ZIP_SIGNATURE_2

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Get MIME type for a file based on its extension.

        Args:
            filename: Name of the file

        Returns:
            MIME type string
        """
        extension = Path(filename).suffix.lower()
        mime_types = {
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".wav": "audio/wav",
            ".flac": "audio/flac",
            ".zip": "application/zip",
        }
        return mime_types.get(extension, "application/octet-stream")

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)

        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.1f} {size_names[i]}"


def get_dj_set_processor_service() -> DJSetProcessorService:
    """Get the singleton API service instance.

    Returns:
        DJSetProcessorService instance
    """
    return DJSetProcessorService()


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
