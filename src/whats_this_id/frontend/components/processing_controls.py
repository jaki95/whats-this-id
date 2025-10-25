"""Processing controls component with real-time progress tracking."""

import streamlit as st
from dj_set_downloader.models.domain_tracklist import DomainTracklist

from whats_this_id.frontend.components.download_section import render_download_section
from whats_this_id.frontend.services.djset_processor import (
    FrontendDJSetProcessorService,
    display_api_error,
    djset_processor_service,
)
from whats_this_id.frontend.state import clear_processing_state


def _check_service_health(api_service: FrontendDJSetProcessorService) -> bool:
    """Check if the DJ set processor service is healthy and display status."""
    is_healthy, message = api_service.check_health()

    if is_healthy:
        st.success(message)
        return True
    else:
        display_api_error(message)
        return False


def _submit_processing_job(
    dj_set_url: str,
    tracklist: DomainTracklist,
    api_service: FrontendDJSetProcessorService,
) -> bool:
    """Submit a new processing job if one isn't already active."""
    if st.session_state.processing_job_id:
        return True  # Job already exists

    success, message, job_id = api_service.submit_processing_job(dj_set_url, tracklist)

    if success:
        st.session_state.processing_job_id = job_id
        st.info(f"Processing job submitted: {job_id}")
        st.rerun()
        return True
    else:
        display_api_error(message, show_service_hint="404" not in message)
        return False


def _handle_job_status_update(
    status, api_service: FrontendDJSetProcessorService
) -> None:
    """Handle different job status states and render appropriate UI."""
    if status.status == "processing":
        # Show progress bar and cancel button
        _render_processing_status(status, api_service)

    elif status.status == "completed":
        st.progress(1.0)
        st.success("✅ Processing completed successfully!")
        render_download_section(st.session_state.processing_job_id)
        st.stop()  # Stop auto-refresh once completed

    elif status.status == "failed":
        st.error(f"Processing failed: {status.error}")
        clear_processing_state()
        st.stop()  # Stop auto-refresh on failure

    elif status.status == "cancelled":
        st.warning("Processing was cancelled")
        clear_processing_state()
        st.stop()  # Stop auto-refresh on cancellation

    else:
        st.warning(f"Unknown status: {status.status}")


def process_dj_set_with_progress(dj_set_url: str, tracklist: DomainTracklist):
    """Process DJ set with real-time progress updates in Streamlit."""

    try:
        if not _check_service_health(djset_processor_service):
            return

        _submit_processing_job(dj_set_url, tracklist, djset_processor_service)

    except Exception as e:
        st.error(f"Error processing DJ set: {e}")
        clear_processing_state()


@st.fragment(run_every=2)
def progress_tracker():
    """Fragment that updates every 2 seconds to show progress."""
    if not st.session_state.processing_job_id:
        st.info("ℹ️ No active processing job")
        return

    try:
        status = djset_processor_service.get_job_status(
            st.session_state.processing_job_id
        )
        st.session_state.processing_status = status
        _handle_job_status_update(status, djset_processor_service)

    except Exception as e:
        st.error(f"Error checking job status: {e}")
        st.stop()  # Stop auto-refresh on error


def _render_processing_status(status, api_service: FrontendDJSetProcessorService):
    """Render the processing status with progress bar and cancel button."""
    progress_value = status.progress / 100.0
    st.progress(progress_value, text=f"{status.progress:.1f}% ({status.message})")

    if st.button("Cancel Processing", use_container_width=True):
        if api_service.cancel_job(st.session_state.processing_job_id):
            st.success("Processing cancelled")
            clear_processing_state()
            st.rerun()
        else:
            st.error("Failed to cancel processing")


def render_processing_controls():
    """Render the DJ set processing controls."""
    split_dj_set_button = st.button(
        "Split DJ Set",
        use_container_width=True,
        help="Split the DJ set into individual tracks",
    )

    if st.session_state.processing_job_id:
        st.subheader("Processing Progress", help=f"{st.session_state.dj_set_url}")
        progress_tracker()  # This will auto-update every 2 seconds
    else:
        st.info("No processing job active")

    if split_dj_set_button:
        if st.session_state.dj_set_url and st.session_state.tracklist:
            process_dj_set_with_progress(
                st.session_state.dj_set_url,
                st.session_state.tracklist,
            )
        else:
            st.warning("Please find the DJ set URL first.")
