"""Search component for tracklist queries."""

import streamlit as st

from whats_this_id.frontend.config import AppConfig
from whats_this_id.frontend.services.search import search_service
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

    with st.spinner(AppConfig.SEARCH_SPINNER_TEXT):
        try:
            # Run search and get multiple results
            search_results = search_service.search_tracklist(
                st.session_state.query_text
            )

            if not search_results:
                st.warning(
                    "🔍 No tracklists found for your query. Try adjusting your search terms or check the spelling."
                )
                st.info(
                    "💡 **Tips for better results:**\n- Include the DJ/artist name and event name\n- Try different variations of the name\n- Be more specific about the event or venue"
                )
            else:
                update_search_results(search_results)

        except Exception as e:
            error_msg = str(e)

            # Provide more user-friendly error messages
            if (
                "net::err_aborted" in error_msg.lower()
                or "err_aborted" in error_msg.lower()
            ):
                st.error(
                    "🚫 Search temporarily blocked: Google is temporarily blocking our requests. This usually resolves itself - please try again in a few minutes."
                )
                st.info(
                    "💡 **What you can do:**\n- Wait 2-3 minutes and try again\n- Try a different search query\n- Check if you have a stable internet connection"
                )
            elif "unable to connect" in error_msg.lower():
                st.error(
                    "🔌 Connection failed: Unable to connect to search services. Please check your internet connection and try again."
                )
            elif "timeout" in error_msg.lower():
                st.error(
                    "⏱️ Request timed out: The search took too long to complete. Please try again with a more specific query."
                )
            elif "blocking requests" in error_msg.lower():
                st.error(
                    "🚫 Access blocked: The website blocked our request. This might be temporary - please try again later."
                )
            elif "no results" in error_msg.lower():
                st.warning(
                    "🔍 No tracklists found: Try adjusting your search query or check the spelling of artist/DJ names."
                )
            else:
                st.error(f"❌ Search failed: {error_msg}")

            st.info(
                "💡 **Tips for better results:**\n- Include the DJ/artist name and event name\n- Try different variations of the name\n- Be more specific about the event or venue"
            )
