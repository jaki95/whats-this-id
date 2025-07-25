"""API service for DJ set processor backend."""

from typing import Optional, Tuple

import streamlit as st
from dj_set_downloader.api.jobs_api import JobsApi
from dj_set_downloader.api.process_api import ProcessApi
from dj_set_downloader.api.system_api import SystemApi
from dj_set_downloader.api_client import ApiClient, Configuration
from dj_set_downloader.models.domain_tracklist import DomainTracklist
from dj_set_downloader.models.job_request import JobRequest

from whats_this_id.frontend.config import AppConfig


class DJSetProcessorService:
    """Service for managing DJ set processor API operations."""

    _instance: Optional["DJSetProcessorService"] = None
    _initialized: bool = False

    def __new__(cls, base_url: str = AppConfig.DEFAULT_API_BASE_URL):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_url: str = AppConfig.DEFAULT_API_BASE_URL):
        """Initialize the API service with configuration (only once)."""
        if not self._initialized:
            config = Configuration(host=base_url)
            self.api_client = ApiClient(configuration=config)
            self.system_api = SystemApi(self.api_client)
            self.process_api = ProcessApi(self.api_client)
            self.jobs_api = JobsApi(self.api_client)
            self._initialized = True

    def check_health(self) -> Tuple[bool, str]:
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
    ) -> Tuple[bool, str, Optional[str]]:
        """Submit a DJ set processing job.

        Returns:
            Tuple of (success, message, job_id)
        """
        try:
            process_response = self.process_api.api_process_post(
                request=JobRequest(
                    url=dj_set_url,
                    tracklist=tracklist,
                    file_extension=file_extension,
                    max_concurrent_tasks=max_concurrent_tasks,
                )
            )
            return True, "Job submitted successfully", process_response.job_id
        except Exception as e:
            if "404" in str(e):
                return False, "DJ Set processor API endpoints not found!", None
            else:
                return False, f"Error submitting processing job: {e}", None

    def get_job_status(self, job_id: str):
        """Get the status of a processing job."""
        try:
            return self.jobs_api.api_jobs_id_get(job_id)
        except Exception as e:
            raise Exception(f"Error checking job status: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a processing job.

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.jobs_api.api_jobs_id_cancel_post(job_id)
        except Exception:
            return False


def get_api_service() -> DJSetProcessorService:
    """Get the singleton API service instance."""
    return DJSetProcessorService()


def display_api_error(message: str, show_service_hint: bool = True):
    """Display a consistent API error message."""
    st.error(message)
    if show_service_hint:
        st.error(
            f"Make sure the DJ set processor service is running on {AppConfig.DEFAULT_API_BASE_URL}"
        )
