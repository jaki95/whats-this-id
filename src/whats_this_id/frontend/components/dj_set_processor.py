"""DJ set processing components with real-time progress tracking."""

import streamlit as st

from whats_this_id.core.downloader.client import DJSetProcessorClient
from whats_this_id.core.models.tracklist import Tracklist
from whats_this_id.frontend.state import clear_processing_state


def process_dj_set_with_progress(dj_set_url: str, tracklist: Tracklist):
    """Process DJ set with real-time progress updates in Streamlit."""
    processor = DJSetProcessorClient()

    try:
        # Check health with better error handling
        try:
            health = processor.health_check()
            st.info(f"🔍 Health check response: {health}")

            status = health.get("status")
            if status not in ["healthy", "ok"]:
                st.error(f"❌ DJ Set processor service is not healthy: {health}")
                return
            else:
                st.success("✅ DJ Set processor service is healthy!")

        except Exception as health_error:
            st.error(
                f"❌ Failed to connect to DJ Set processor service: {health_error}"
            )
            st.error("Make sure the service is running on http://localhost:8000")
            return

        # Submit job only if we don't have one already
        if not st.session_state.processing_job_id:
            try:
                job_id = processor.process_set(
                    download_url=dj_set_url,
                    tracklist=tracklist,
                    file_extension="m4a",
                    max_concurrent_tasks=4,
                )
                st.session_state.processing_job_id = job_id
                st.info(f"🚀 Processing job submitted: {job_id}")
                st.rerun()

            except Exception as process_error:
                if "404" in str(process_error):
                    st.error("❌ DJ Set processor API endpoints not found!")
                else:
                    st.error(f"❌ Error submitting processing job: {process_error}")
                return

    except Exception as e:
        st.error(f"Error processing DJ set: {e}")
        clear_processing_state()


@st.fragment(run_every=2)
def progress_tracker():
    """Fragment that updates every 2 seconds to show progress."""
    if not st.session_state.processing_job_id:
        st.info("ℹ️ No active processing job")
        return

    processor = DJSetProcessorClient()

    try:
        status = processor.get_job_status(st.session_state.processing_job_id)
        st.session_state.processing_status = status

        if status.status == "processing":
            # Show progress bar
            progress_value = status.progress / 100.0
            st.progress(
                progress_value, text=f"{status.progress:.1f}% ({status.message})"
            )

            # Add cancel button if processing
            if st.button("❌ Cancel Processing", use_container_width=True):
                if processor.cancel_job(st.session_state.processing_job_id):
                    st.success("Processing cancelled")
                    clear_processing_state()
                    st.rerun()
                else:
                    st.error("Failed to cancel processing")

        elif status.status == "completed":
            st.progress(1.0)
            st.success("✅ Processing completed successfully!")

            if status.results:
                st.success("🎵 Output files created:")
                for file_path in status.results:
                    st.code(file_path)

            # Clear job state
            clear_processing_state()

        elif status.status == "failed":
            st.error(f"❌ Processing failed: {status.error}")
            clear_processing_state()

        elif status.status == "cancelled":
            st.warning("⚠️ Processing was cancelled")
            clear_processing_state()

        else:
            st.warning(f"⚠️ Unknown status: {status.status}")

    except Exception as e:
        st.error(f"❌ Error checking job status: {e}")
        st.error(f"🔍 Exception details: {type(e).__name__}: {str(e)}")


def render_processing_section():
    """Render the DJ set processing section."""
    # Split DJ Set button
    split_dj_set_button = st.button(
        "Split DJ Set",
        use_container_width=True,
        help="Split the DJ set into individual tracks",
    )

    # Display processing status with live updates
    if st.session_state.processing_job_id:
        st.subheader("Processing Progress", help=f"{st.session_state.dj_set_url}")
        progress_tracker()  # This will auto-update every 2 seconds
    else:
        st.info("No processing job active")

    # Handle split DJ set
    if split_dj_set_button:
        if st.session_state.dj_set_url and st.session_state.tracklist:
            process_dj_set_with_progress(
                st.session_state.dj_set_url, st.session_state.tracklist
            )
        else:
            st.warning("Please find the DJ set URL first.")
