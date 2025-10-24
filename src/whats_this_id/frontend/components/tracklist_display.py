"""Tracklist display components for rendering tracklist information and tracks."""

import pandas as pd
import streamlit as st
from dj_set_downloader import DomainTracklist


def render_tracklist_display(tracklist: DomainTracklist):
    """Render the tracklist display with metadata and tracks."""
    # Tracklist information
    st.header(f"{tracklist.name} - {tracklist.artist}")

    # Tracklist metadata in a nice format
    metadata_cols = st.columns(2)
    with metadata_cols[0]:
        st.markdown(f"**Year:** {tracklist.year}")
        st.markdown(f"**Soundcloud link:** {st.session_state.dj_set_url}")
    with metadata_cols[1]:
        st.markdown(f"**Genre:** {tracklist.genre}")
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
