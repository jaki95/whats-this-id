"""Results section component for displaying tracklist and processing options."""

import streamlit as st

from whats_this_id.frontend.components.processing_controls import (
    render_processing_controls,
)
from whats_this_id.frontend.components.tracklist_display import render_tracklist_display
from whats_this_id.frontend.config import AppConfig


def render_results_section():
    """Render the results section with tracklist and processing options."""
    if not st.session_state.tracklist:
        return

    tracklist = st.session_state.tracklist

    # Create two columns for layout using config
    col1, col2 = st.columns(AppConfig.TRACKLIST_RESULTS_COLUMNS)

    with col1:
        render_tracklist_display(tracklist)

    with col2:
        render_processing_controls()
