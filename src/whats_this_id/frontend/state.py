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
    if "download_in_progress" not in st.session_state:
        st.session_state.download_in_progress = False
    if "downloaded_files" not in st.session_state:
        st.session_state.downloaded_files = []


def clear_processing_state():
    """Clear processing-related session state."""
    st.session_state.processing_job_id = None
    st.session_state.processing_status = None


def clear_download_state():
    """Clear download-related session state."""
    st.session_state.download_in_progress = False
    st.session_state.downloaded_files = []
    
    # Clear any prepared download data
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith("download_data_") or key.startswith("track_data_"):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]


def update_search_results(tracklist, dj_set_url):
    """Update session state with search results."""
    st.session_state.tracklist = tracklist
    st.session_state.dj_set_url = dj_set_url
    # Clear any existing processing/download state when new search is performed
    clear_processing_state()
    clear_download_state()
