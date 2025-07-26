"""Download section component for completed processing jobs."""

import streamlit as st

from whats_this_id.frontend.services import get_dj_set_processor_service
from whats_this_id.frontend.state import clear_processing_state


def render_download_section(job_id: str, status) -> None:
    """Render the download section for completed jobs.

    Args:
        job_id: The completed processing job ID
        status: The job status object with results
    """
    processor_service = get_dj_set_processor_service()

    st.subheader("📥 Download Processed Tracks")

    # Get tracks information
    tracks_info = processor_service.get_tracks_info(job_id)

    if tracks_info:
        _render_tracks_download_options(job_id, tracks_info, processor_service)
    else:
        _render_basic_download_options(job_id, status, processor_service)

    # Clear job state button
    if st.button("🧹 Clear Results", use_container_width=True):
        clear_processing_state()
        st.rerun()


def _render_tracks_download_options(
    job_id: str, tracks_info, processor_service
) -> None:
    """Render download options when detailed track info is available."""

    # Download all tracks as ZIP
    st.markdown("### 📦 Download All Tracks")
    if st.button("⬇️ Download All as ZIP", use_container_width=True):
        with st.spinner("Preparing ZIP file..."):
            result = processor_service.download_all_tracks(job_id)
            if result:
                file_data, filename = result
                st.download_button(
                    label=f"💾 Save {filename} ({processor_service.format_file_size(len(file_data))})",
                    data=file_data,
                    file_name=filename,
                    mime=processor_service.get_mime_type(filename),
                    use_container_width=True,
                )
                st.success("✅ ZIP file ready for download!")

    # Individual track downloads
    if hasattr(tracks_info, 'tracks') and tracks_info.tracks:
        st.markdown("### 🎵 Download Individual Tracks")

        for i, track in enumerate(tracks_info.tracks):
            track_name = getattr(track, 'name', f"Track {i+1}")
            file_size = getattr(track, 'file_size', 0)

            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"🎧 **{track_name}**")
                if file_size > 0:
                    st.caption(f"Size: {processor_service.format_file_size(file_size)}")

            with col2:
                if st.button(
                    f"⬇️", key=f"download_{track_name}_{i}", help=f"Download {track_name}"
                ):
                    with st.spinner(f"Downloading {track_name}..."):
                        result = processor_service.download_single_track(
                            job_id, i + 1  # Track numbers are usually 1-indexed
                        )
                        if result:
                            file_data, filename = result
                            st.download_button(
                                label=f"💾 Save {filename}",
                                data=file_data,
                                file_name=filename,
                                mime=processor_service.get_mime_type(filename),
                                key=f"save_{track_name}_{i}",
                            )


def _render_basic_download_options(job_id: str, status, processor_service) -> None:
    """Render basic download options when detailed track info is unavailable."""

    # Try to download all tracks as ZIP
    if st.button("⬇️ Download All Tracks", use_container_width=True):
        with st.spinner("Preparing download..."):
            result = processor_service.download_all_tracks(job_id)
            if result:
                file_data, filename = result
                st.download_button(
                    label=f"💾 Save {filename} ({processor_service.format_file_size(len(file_data))})",
                    data=file_data,
                    file_name=filename,
                    mime=processor_service.get_mime_type(filename),
                    use_container_width=True,
                )
                st.success("✅ Download ready!")

    # Show legacy file paths if available
    if hasattr(status, "results") and status.results:
        with st.expander("📁 Raw Output Files (Advanced)"):
            st.write("Legacy file paths:")
            for file_path in status.results:
                st.code(file_path)
