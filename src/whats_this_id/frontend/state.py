"""Session state management for the What's This ID app."""

import streamlit as st


def initialize_session_state():
    """Initialize all session state variables."""
    if "query_text" not in st.session_state:
        st.session_state.query_text = ""
    if "tracklist" not in st.session_state:
        st.session_state.tracklist = None
    if "dj_set_url" not in st.session_state:
        st.session_state.dj_set_url = None
    if "processing_job_id" not in st.session_state:
        st.session_state.processing_job_id = None
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = None


def clear_processing_state():
    """Clear processing-related session state."""
    st.session_state.processing_job_id = None
    st.session_state.processing_status = None


def update_search_results(tracklist, dj_set_url):
    """Update session state with search results."""
    st.session_state.tracklist = tracklist
    st.session_state.dj_set_url = dj_set_url
