"""DJ set processing components with real-time progress tracking."""

import streamlit as st
from dj_set_downloader.api.jobs_api import JobsApi
from dj_set_downloader.api.process_api import ProcessApi
from dj_set_downloader.api.system_api import SystemApi
from dj_set_downloader.api_client import ApiClient
from dj_set_downloader.models.domain_tracklist import DomainTracklist
from dj_set_downloader.models.job_request import JobRequest

from whats_this_id.frontend.state import clear_processing_state


def process_dj_set_with_progress(
    system_api: SystemApi,
    process_api: ProcessApi,
    dj_set_url: str,
    tracklist: DomainTracklist,
):
    """Process DJ set with real-time progress updates in Streamlit."""

    try:
        try:
            health = system_api.health_get()
            st.info(f"Health check response: {health}")

            status = health.status
            if status not in ["healthy", "ok"]:
                st.error(f"DJ Set processor service is not healthy: {health}")
                return
            else:
                st.success("DJ Set processor service is healthy!")

        except Exception as health_error:
            st.error(f"Failed to connect to DJ Set processor service: {health_error}")
            st.error("Make sure the service is running on http://localhost:8000")
            return

        # Submit job only if we don't have one already
        if not st.session_state.processing_job_id:
            try:
                process_response = process_api.api_process_post(
                    request=JobRequest(
                        url=dj_set_url,
                        tracklist=tracklist,
                        file_extension="m4a",
                        max_concurrent_tasks=4,
                    )
                )
                st.session_state.processing_job_id = process_response.job_id
                st.info(f"Processing job submitted: {process_response.job_id}")
                st.rerun()

            except Exception as process_error:
                if "404" in str(process_error):
                    st.error("DJ Set processor API endpoints not found!")
                else:
                    st.error(f"Error submitting processing job: {process_error}")
                return

    except Exception as e:
        st.error(f"Error processing DJ set: {e}")
        clear_processing_state()


@st.fragment(run_every=2)
def progress_tracker(jobs_api: JobsApi):
    """Fragment that updates every 2 seconds to show progress."""
    if not st.session_state.processing_job_id:
        st.info("ℹ️ No active processing job")
        return

    try:
        status = jobs_api.api_jobs_id_get(st.session_state.processing_job_id)
        st.session_state.processing_status = status

        if status.status == "processing":
            # Show progress bar
            progress_value = status.progress / 100.0
            st.progress(
                progress_value, text=f"{status.progress:.1f}% ({status.message})"
            )

            # Add cancel button if processing
            if st.button("Cancel Processing", use_container_width=True):
                if jobs_api.api_jobs_id_cancel_post(st.session_state.processing_job_id):
                    st.success("Processing cancelled")
                    clear_processing_state()
                    st.rerun()
                else:
                    st.error("Failed to cancel processing")

        elif status.status == "completed":
            st.progress(1.0)
            st.success("Processing completed successfully!")

            if status.results:
                st.success("Output files created:")
                for file_path in status.results:
                    st.code(file_path)

            # Clear job state
            clear_processing_state()

        elif status.status == "failed":
            st.error(f"Processing failed: {status.error}")
            clear_processing_state()

        elif status.status == "cancelled":
            st.warning("Processing was cancelled")
            clear_processing_state()

        else:
            st.warning(f"Unknown status: {status.status}")

    except Exception as e:
        st.error(f"Error checking job status: {e}")
        st.error(f"Exception details: {type(e).__name__}: {str(e)}")


def render_processing_section():
    """Render the DJ set processing section."""
    api_client = ApiClient()
    system_api = SystemApi(api_client)
    process_api = ProcessApi(api_client)
    jobs_api = JobsApi(api_client)

    # Split DJ Set button
    split_dj_set_button = st.button(
        "Split DJ Set",
        use_container_width=True,
        help="Split the DJ set into individual tracks",
    )

    # Display processing status with live updates
    if st.session_state.processing_job_id:
        st.subheader("Processing Progress", help=f"{st.session_state.dj_set_url}")
        progress_tracker(jobs_api)  # This will auto-update every 2 seconds
    else:
        st.info("No processing job active")

    # Handle split DJ set
    if split_dj_set_button:
        if st.session_state.dj_set_url and st.session_state.tracklist:
            process_dj_set_with_progress(
                system_api,
                process_api,
                st.session_state.dj_set_url,
                st.session_state.tracklist,
            )
        else:
            st.warning("Please find the DJ set URL first.")
