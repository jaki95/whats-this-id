"""Tracklist display components for rendering tracklist information and tracks."""

import logging

import pandas as pd
import streamlit as st
from dj_set_downloader import DomainTracklist

from whats_this_id.core.services import extract_metadata

logger = logging.getLogger(__name__)


def render_tracklist_display(tracklist: DomainTracklist):
    """Render the tracklist display with metadata and tracks."""
    # AI Extraction button
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🤖 Extract Metadata with AI", use_container_width=True):
                _handle_ai_extraction(tracklist)

    # Tracklist information
    st.header(f"{tracklist.name}")

    # Tracklist metadata in a nice format
    metadata_cols = st.columns(2)
    with metadata_cols[0]:
        st.markdown(f"**Artist:** {tracklist.artist}")
        st.markdown(f"**Set link:** {st.session_state.dj_set_url}")
    with metadata_cols[1]:
        st.markdown(f"**Year:** {tracklist.year}")
        track_count = len(tracklist.tracks) if tracklist.tracks else 0
        st.markdown(f"**Total Tracks:** {track_count}")

    st.markdown("---")

    # Scrollable tracklist container
    with st.container():
        # Create a scrollable area for tracks
        if tracklist.tracks:
            tracks_data = []
            for i, track in enumerate(tracklist.tracks):
                tracks_data.append(
                    {
                        "#": i + 1,
                        "Track": track.name,
                        "Artist": track.artist,
                        "Start": track.start_time,
                        "End": track.end_time,
                    }
                )

            # Display as a dataframe for better scrolling
            df = pd.DataFrame(tracks_data)
            st.dataframe(df, use_container_width=True, height=400, hide_index=True)
        else:
            st.info("No tracks found in this tracklist.")


def _handle_ai_extraction(tracklist: DomainTracklist) -> None:
    """Handle AI metadata extraction from the tracklist title.

    Args:
        tracklist: The tracklist to extract metadata from.
    """
    with st.spinner("🤖 Extracting metadata with AI..."):
        try:
            extracted = extract_metadata(tracklist.name)
            tracklist.artist = extracted.artist
            if extracted.year is not None:
                tracklist.year = extracted.year
            st.rerun()
        except ValueError as e:
            st.error(
                f"Configuration error: {e}\n\n"
                "Please set your OPENAI_API_KEY in a .env file."
            )
            logger.error(f"Configuration error during extraction: {e}")
        except Exception as e:
            st.error(f"Failed to extract metadata: {e}")
            logger.error(f"Error during metadata extraction: {e}")
