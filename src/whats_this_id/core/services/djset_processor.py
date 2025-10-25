"""Core API service for DJ set processor backend."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Optional

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

# Constants for ZIP file validation
ZIP_SIGNATURE_1 = b"PK\x03\x04"  # Standard ZIP file signature
ZIP_SIGNATURE_2 = b"PK\x05\x06"  # Empty ZIP file signature
MIN_ZIP_SIZE = 4  # Minimum bytes needed to validate ZIP signature


class DJSetProcessorService:
    """Core service for managing DJ set processor API operations."""

    def __init__(self, base_url: str) -> None:
        config = Configuration(host=base_url)
        self.api_client = ApiClient(configuration=config)
        self.system_api = SystemApi(self.api_client)
        self.process_api = ProcessApi(self.api_client)
        self.jobs_api = JobsApi(self.api_client)
        self.downloads_api = DownloadsApi(self.api_client)

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
        file_extension: str = "mp3",
        max_concurrent_tasks: int = 5,
    ) -> tuple[bool, str, str | None]:
        """Submit a DJ set processing job.

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
            if response.status_code != HTTPStatus.ACCEPTED:
                error_msg = f"Error submitting processing job: {response.status_code}"
                return False, error_msg, None

            return True, "Job submitted successfully", response.data.job_id
        except Exception as e:
            error_msg = f"Error submitting processing job: {e}"
            return False, error_msg, None

    def get_job_status(self, job_id: str) -> JobStatus | None:
        """Get the status of a processing job.

        Returns:
            JobStatus object if successful, None if failed
        """
        try:
            response = self.jobs_api.api_jobs_id_get_with_http_info(job_id)
            if response.status_code != HTTPStatus.OK:
                return None
            return response.data
        except Exception as e:
            raise Exception(f"Error checking job status: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a processing job.

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.jobs_api.api_jobs_id_cancel_post_with_http_info(job_id)
            if response.status_code != HTTPStatus.OK:
                return False
            return True
        except Exception:
            return False

    def download_all_tracks(self, job_id: str) -> Optional[tuple[bytearray, str]]:
        """Download all tracks as ZIP with proper error handling.

        Returns:
            Tuple of (file_data, filename) if successful, None if failed
        """
        try:
            response = self.downloads_api.api_jobs_id_download_get_with_http_info(
                job_id
            )
            if response.status_code != HTTPStatus.OK:
                return None

            filename = "tracks.zip"

            if not self._is_valid_zip_file(response.data):
                return None

            return response.data, filename

        except Exception:
            return None

    def download_single_track(
        self, job_id: str, track_number: int, file_extension: str = "mp3"
    ) -> tuple[bytearray, str] | None:
        """Download a single track file.

        Returns:
            Tuple of (file_data, filename) if successful, None if failed
        """
        try:
            response = self.downloads_api.api_jobs_id_tracks_track_number_download_get_with_http_info(
                job_id, track_number
            )
            if response.status_code != HTTPStatus.OK:
                return None

            filename = f"track_{track_number}.{file_extension}"
            return response.data, filename

        except Exception:
            return None

    def get_tracks_info(self, job_id: str) -> JobTracksInfoResponse | None:
        """Get detailed track information for a completed job.

        Returns:
            JobTracksInfoResponse object if successful, None if failed
        """
        try:
            response = self.downloads_api.api_jobs_id_tracks_get_with_http_info(job_id)
            if response.status_code != HTTPStatus.OK:
                return None
            return response.data
        except Exception:
            return None

    def _is_valid_zip_file(self, file_data: bytes | bytearray | None) -> bool:
        """Validate if the given data represents a valid ZIP file.

        Returns:
            True if valid ZIP file, False otherwise
        """
        if not file_data or len(file_data) < MIN_ZIP_SIZE:
            return False

        return file_data[:4] == ZIP_SIGNATURE_1 or file_data[:4] == ZIP_SIGNATURE_2

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Get MIME type for a file based on its extension.

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
