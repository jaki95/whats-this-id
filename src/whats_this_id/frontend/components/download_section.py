"""Download section component for completed processing jobs."""

import streamlit as st

from whats_this_id.frontend.services import get_dj_set_processor_service
from whats_this_id.frontend.services.dj_set_processor import (
    DJSetProcessorService,
    JobTracksInfoResponse,
)


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


def render_download_section(job_id: str) -> None:
    """Render the download section for completed jobs.

    Args:
        job_id: The completed processing job ID
    """
    processor_service = get_dj_set_processor_service()

    st.subheader("Download Processed Tracks")

    tracks_info = processor_service.get_tracks_info(job_id)

    if tracks_info:
        _render_tracks_download_options(job_id, tracks_info, processor_service)


def _render_tracks_download_options(
    job_id: str,
    tracks_info: JobTracksInfoResponse,
    processor_service: DJSetProcessorService,
) -> None:
    """Render download options when detailed track info is available."""

    st.markdown("### Download All Tracks")

    zip_data_key = f"download_data_{job_id}_zip"

    if zip_data_key in st.session_state:
        file_data, filename = st.session_state[zip_data_key]
        _create_download_button(file_data, filename, processor_service)

    else:
        if st.button("Download All Tracks", use_container_width=True):
            with st.spinner("Preparing download..."):
                result = processor_service.download_all_tracks(job_id)
                if result:
                    file_data, original_filename = result
                    if (
                        hasattr(st.session_state, "tracklist")
                        and st.session_state.tracklist
                    ):
                        tracklist_name = st.session_state.tracklist.name
                    if tracklist_name:
                        safe_name = (
                            "".join(
                                c
                                for c in tracklist_name
                                if c.isalnum() or c in (" ", "-", "_")
                            )
                            .strip()
                            .replace(" ", "_")
                        )
                        new_filename = f"{safe_name}.zip"
                    else:
                        new_filename = original_filename

                    st.session_state[zip_data_key] = (file_data, new_filename)
                    st.rerun()

    # Individual tracks section
    if not hasattr(tracks_info, "tracks") or not tracks_info.tracks:
        return

    st.markdown("### Download Individual Tracks")

    for i, track in enumerate(tracks_info.tracks):
        track_name = getattr(track, "name", f"Track {i + 1}")
        file_size = getattr(track, "file_size", 0)
        track_data_key = f"track_data_{job_id}_{i}"

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**{track_name}**")
            if file_size > 0:
                st.caption(f"Size: {processor_service.format_file_size(file_size)}")

        with col2:
            if track_data_key in st.session_state:
                file_data, filename = st.session_state[track_data_key]
                _create_download_button(file_data, filename, processor_service, "💾")
            else:
                if st.button("⬇️", key=f"download_{i}", help=f"Download {track_name}"):
                    with st.spinner(f"Preparing {track_name}..."):
                        result = processor_service.download_single_track(job_id, i + 1)
                        if result:
                            file_data, original_filename = result
                            ext = (
                                original_filename.split(".")[-1]
                                if "." in original_filename
                                else "mp3"
                            )
                            safe_name = "".join(
                                c
                                for c in track_name
                                if c.isalnum() or c in (" ", "-", "_")
                            ).strip()
                            filename = f"{safe_name}.{ext}"
                            st.session_state[track_data_key] = (file_data, filename)
                            st.rerun()
