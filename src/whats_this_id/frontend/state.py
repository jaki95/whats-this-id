"""Session state management for the What's This ID app."""

import streamlit as st


def initialize_session_state():
    """Initialize all session state variables."""
    if "query_text" not in st.session_state:
        st.session_state.query_text = ""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "selected_result_index" not in st.session_state:
        st.session_state.selected_result_index = None
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


def clear_download_state():
    """Clear download-related session state."""
    # Clear any prepared download data
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith("download_data_") or key.startswith("track_data_"):
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del st.session_state[key]


def update_search_results(search_results):
    """Update session state with multiple search results."""
    st.session_state.search_results = search_results
    st.session_state.selected_result_index = None
    st.session_state.tracklist = None
    st.session_state.dj_set_url = None
    # Clear any existing processing/download state when new search is performed
    clear_processing_state()
    clear_download_state()


def select_search_result(index: int):
    """Select a specific search result and update the tracklist."""
    if 0 <= index < len(st.session_state.search_results):
        st.session_state.selected_result_index = index
        # The tracklist and URL will be fetched when needed
        st.session_state.tracklist = None
        st.session_state.dj_set_url = None
