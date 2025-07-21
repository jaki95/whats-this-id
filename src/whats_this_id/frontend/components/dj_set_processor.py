"""DJ set processing components with real-time progress tracking."""

import streamlit as st

from whats_this_id.core.downloader.client import DJSetProcessorClient
from whats_this_id.core.models.tracklist import Tracklist
from whats_this_id.frontend.state import clear_processing_state, clear_download_state
from whats_this_id.frontend.utils.download_helpers import (
    safe_download_all_tracks,
    safe_download_track,
    get_mime_type,
    format_file_size,
)


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


def render_download_all_button(job_id: str):
    """Render download all tracks button with direct download."""
    
    # Check if we have cached download data for this job
    download_data_key = f"download_data_{job_id}"
    
    # Fetch data if not already cached
    if download_data_key not in st.session_state:
        with st.spinner("📦 Loading download data..."):
            result = safe_download_all_tracks(job_id)
            if result:
                st.session_state[download_data_key] = result
            else:
                st.error("❌ Failed to load download data")
                return
    
    # Get the cached data
    file_data, filename = st.session_state[download_data_key]
    
    # Direct download button - single click downloads immediately
    if st.download_button(
        label="📦 Download All Tracks (ZIP)",
        data=file_data,
        file_name=filename,
        mime=get_mime_type(filename),
        use_container_width=True,
        key=f"download_zip_{job_id}"
    ):
        # Only add to downloaded files when button is actually clicked
        if filename not in st.session_state.downloaded_files:
            st.session_state.downloaded_files.append(filename)
        st.success(f"✅ Download started: {filename}")


def render_individual_download_button(job_id: str, track_number: int, track_name: str):
    """Render individual track download button with direct download."""
    
    # Check if we have cached download data for this track
    download_data_key = f"track_data_{job_id}_{track_number}"
    
    # Fetch data if not already cached
    if download_data_key not in st.session_state:
        with st.spinner(f"🎵 Loading track {track_number}..."):
            result = safe_download_track(job_id, track_number)
            if result:
                st.session_state[download_data_key] = result
            else:
                st.error(f"❌ Failed to load track {track_number}")
                return
    
    # Get the cached data
    file_data, filename = st.session_state[download_data_key]
    
    # Direct download button - single click downloads immediately
    if st.download_button(
        label="⬇️",
        data=file_data,
        file_name=filename,
        mime=get_mime_type(filename),
        key=f"download_track_file_{track_number}",
        help=f"Download {track_name}"
    ):
        # Only add to downloaded files when button is actually clicked
        if filename not in st.session_state.downloaded_files:
            st.session_state.downloaded_files.append(filename)
        st.success(f"✅ Download started: {filename}")


def render_download_section(job_id: str, status):
    """Render the download section with track information and download options."""
    st.subheader("🎵 Available Tracks")
    
    if status.tracks:
        # Show summary
        available_tracks = [track for track in status.tracks if track.available]
        total_size = sum(track.size_bytes for track in available_tracks)
        
        st.info(f"📊 {len(available_tracks)} of {status.total_tracks} tracks available • Total size: {format_file_size(total_size)}")
        
        # Download all tracks button
        col1, col2 = st.columns([2, 1])
        with col1:
            render_download_all_button(job_id)
        
        with col2:
            if st.button("🔄 Clear Downloads", use_container_width=True):
                clear_download_state()
                st.rerun()
        
        # Show downloaded files summary if any
        if st.session_state.downloaded_files:
            with st.expander(f"📥 Downloaded Files ({len(st.session_state.downloaded_files)})"):
                for filename in st.session_state.downloaded_files:
                    st.write(f"✅ {filename}")
        
        # Individual track list
        st.subheader("Individual Tracks")
        
        for track in status.tracks:
            status_icon = "✅" if track.available else "❌"
            
            # Create columns for track info and download button
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if track.available:
                    st.write(f"{status_icon} **{track.track_number}.** {track.artist} - {track.name}")
                    st.caption(f"⏱️ {track.start_time} - {track.end_time} • 📁 {format_file_size(track.size_bytes)}")
                else:
                    st.write(f"{status_icon} **{track.track_number}.** {track.artist} - {track.name} *(unavailable)*")
                    st.caption(f"⏱️ {track.start_time} - {track.end_time}")
            
            with col2:
                if track.available:
                    render_individual_download_button(job_id, track.track_number, f"{track.artist} - {track.name}")
                else:
                    st.button("❌", disabled=True, help="Track not available", key=f"unavailable_{track.track_number}")
            
            st.divider()
    
    else:
        st.warning("No track information available. This might be an older job or the tracks data is not yet populated.")


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

            # Show download section
            render_download_section(st.session_state.processing_job_id, status)

            # Optionally show old results format for backward compatibility
            if status.results:
                with st.expander("📁 Raw Output Files (Advanced)"):
                    st.write("Legacy file paths:")
                    for file_path in status.results:
                        st.code(file_path)
            
            # STOP auto-refresh once completed
            st.stop()

        elif status.status == "failed":
            st.error(f"❌ Processing failed: {status.error}")
            clear_processing_state()
            # STOP auto-refresh on failure
            st.stop()

        elif status.status == "cancelled":
            st.warning("⚠️ Processing was cancelled")
            clear_processing_state()
            # STOP auto-refresh on cancellation
            st.stop()

        else:
            st.warning(f"⚠️ Unknown status: {status.status}")

    except Exception as e:
        st.error(f"❌ Error checking job status: {e}")
        st.error(f"🔍 Exception details: {type(e).__name__}: {str(e)}")
        # STOP auto-refresh on error
        st.stop()


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
