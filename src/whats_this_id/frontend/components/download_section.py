"""Download section component for completed processing jobs."""

import streamlit as st

from whats_this_id.frontend.services import get_dj_set_processor_service
from whats_this_id.frontend.state import clear_processing_state

from whats_this_id.frontend.services.dj_set_processor import DJSetProcessorService, JobTracksInfoResponse


def _create_download_button(
    file_data: bytes, filename: str, processor_service, label_prefix: str = "💾 Save"
) -> None:
    """Create a standardized download button with file size and proper MIME type.

    Args:
        file_data: The file data to download
        filename: Name of the file
        processor_service: The DJ set processor service instance
        label_prefix: Prefix for the button label
    """
    file_size = processor_service.format_file_size(len(file_data))
    st.download_button(
        label=f"{label_prefix} {filename} ({file_size})",
        data=file_data,
        file_name=filename,
        mime=processor_service.get_mime_type(filename),
        use_container_width=True,
    )


def render_download_section(job_id: str, status) -> None:
    """Render the download section for completed jobs.

    Args:
        job_id: The completed processing job ID
        status: The job status object with results
    """
    processor_service = get_dj_set_processor_service()

    st.subheader("Download Processed Tracks")

    tracks_info = processor_service.get_tracks_info(job_id)

    if tracks_info:
        _render_tracks_download_options(job_id, tracks_info, processor_service)


def _render_tracks_download_options(
    job_id: str, tracks_info: JobTracksInfoResponse, processor_service: DJSetProcessorService
) -> None:
    """Render download options when detailed track info is available."""

    st.markdown("### Download All Tracks")
    if st.button("Download All as ZIP", use_container_width=True):
        with st.spinner("Preparing ZIP file..."):
            result = processor_service.download_all_tracks(job_id)
            if result:
                file_data, filename = result
                _create_download_button(file_data, filename, processor_service)
                st.success("✅ ZIP file ready for download!")

    if hasattr(tracks_info, "tracks") and tracks_info.tracks:
        st.markdown("### Download Individual Tracks")

        for i, track in enumerate(tracks_info.tracks):
            track_name = getattr(track, "name", f"Track {i + 1}")
            file_size = getattr(track, "file_size", 0)

            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**{track_name}**")
                if file_size > 0:
                    st.caption(f"Size: {processor_service.format_file_size(file_size)}")

            with col2:
                if st.button(
                    "⬇️",
                    key=f"download_{track_name}_{i}",
                    help=f"Download {track_name}",
                ):
                    with st.spinner(f"Downloading {track_name}..."):
                        result = processor_service.download_single_track(
                            job_id,
                            i + 1,  # Track numbers are usually 1-indexed
                        )
                        if result:
                            file_data, filename = result
                            _create_download_button(
                                file_data,
                                filename,
                                processor_service,
                                label_prefix="💾",
                            )
