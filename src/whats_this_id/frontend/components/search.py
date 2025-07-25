"""Search component for tracklist queries."""

import asyncio

import streamlit as st

from whats_this_id.frontend.config import AppConfig
from whats_this_id.frontend.services import get_search_service
from whats_this_id.frontend.state import update_search_results


def render_search_section():
    """Render the search section of the app."""
    st.header("Search Tracklists")

    # Search input
    query = st.text_area(
        label="",
        value=st.session_state.query_text,
        placeholder=AppConfig.SEARCH_PLACEHOLDER,
        height=100,
        key="query_input",
    )

    # Update session state when text area changes
    if query != st.session_state.query_text:
        st.session_state.query_text = query

    # Search button with centered layout
    col1, col2, col3 = st.columns(AppConfig.SEARCH_BUTTON_COLUMNS)
    with col2:
        search_button = st.button(
            AppConfig.SEARCH_BUTTON_TEXT, type="primary", use_container_width=True
        )

    # Handle search
    if search_button:
        _handle_search_action()


def _handle_search_action():
    """Handle the search button action."""
    if not st.session_state.query_text.strip():
        st.warning("Please enter a search query.")
        return

    search_service = get_search_service()

    with st.spinner(AppConfig.SEARCH_SPINNER_TEXT):
        try:
            # Run both searches concurrently
            result, dj_set_url = asyncio.run(
                search_service.search_tracklist_and_soundcloud(
                    st.session_state.query_text
                )
            )
            update_search_results(result.pydantic, dj_set_url)

        except Exception as e:
            st.error(f"Search failed: {e}")
            st.error("Please try again or check your query.")
