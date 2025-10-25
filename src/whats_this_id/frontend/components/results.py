"""Results section component for displaying tracklist and processing options."""

import streamlit as st

from whats_this_id.core.services import search_service
from whats_this_id.frontend.components.processing_controls import (
    render_processing_controls,
)
from whats_this_id.frontend.components.tracklist_display import render_tracklist_display
from whats_this_id.frontend.config import AppConfig


def render_results_section():
    """Render the results section with tracklist and processing options."""
    # Only show if a result is selected
    if st.session_state.selected_result_index is None:
        return

    # If tracklist is not loaded yet, fetch it
    if not st.session_state.tracklist:
        with st.spinner("Loading tracklist details..."):
            try:
                selected_result = st.session_state.search_results[
                    st.session_state.selected_result_index
                ]
                tracklist, dj_set_url = search_service.get_tracklist(
                    selected_result.link
                )
                st.session_state.tracklist = tracklist
                st.session_state.dj_set_url = dj_set_url
            except Exception as e:
                st.error(f"Failed to load tracklist: {e}")
                return

    tracklist = st.session_state.tracklist

    # Create two columns for layout using config
    col1, col2 = st.columns(AppConfig.TRACKLIST_RESULTS_COLUMNS)

    with col1:
        render_tracklist_display(tracklist)

    with col2:
        render_processing_controls()
