"""Main Streamlit application for What's This ID."""

import streamlit as st

from whats_this_id.frontend.components.dj_set_processor import render_processing_section
from whats_this_id.frontend.components.tracklist_display import render_tracklist_display
from whats_this_id.frontend.state import initialize_session_state, update_search_results
from whats_this_id.frontend.utils.async_search import search_tracklist_and_soundcloud_sync

# Page configuration
st.set_page_config(
    page_title="What's This ID?",
    page_icon="💿",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_search_section():
    """Render the search section of the app."""
    st.header("Search Tracklists")

    # Search input
    query = st.text_area(
        label="",
        value=st.session_state.query_text,
        placeholder="Enter your tracklist search query:",
        height=100,
        key="query_input",
    )

    # Update session state when text area changes
    if query != st.session_state.query_text:
        st.session_state.query_text = query

    # Search button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        search_button = st.button(
            "Search Tracklists", type="primary", use_container_width=True
        )

    # Handle search
    if search_button:
        if st.session_state.query_text.strip():
            with st.spinner(
                "🤖 AI agents are searching for tracklists and SoundCloud..."
            ):
                # Run both searches concurrently
                result, dj_set_url = search_tracklist_and_soundcloud_sync(st.session_state.query_text)
                update_search_results(result.pydantic, dj_set_url)
        else:
            st.warning("Please enter a search query.")


def render_results_section():
    """Render the results section with tracklist and processing options."""
    if not st.session_state.tracklist:
        return

    tracklist = st.session_state.tracklist

    # Create two columns for layout
    col1, col2 = st.columns([2, 1])

    with col1:
        render_tracklist_display(tracklist)

    with col2:
        render_processing_section()


def main():
    """Main application function."""
    # Header
    st.title("💿 What's This ID?")
    st.markdown(
        "Find the IDs of a DJ set using natural language queries with AI-powered multi-agent orchestration"
    )

    # Initialize session state
    initialize_session_state()

    # Render sections
    render_search_section()
    render_results_section()


if __name__ == "__main__":
    main()
