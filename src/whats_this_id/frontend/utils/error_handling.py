"""Error handling utilities for the frontend."""

import streamlit as st


def display_search_error(error_msg: str) -> None:
    """Display user-friendly search error messages.

    Args:
        error_msg: The error message to display
    """
    st.error(f"❌ Search failed: {error_msg}")

    # Always show tips for better results
    st.info(
        "💡 **Tips for better results:**\n- Include the DJ/artist name and event name\n- Try different variations of the name\n- Be more specific about the event or venue"
    )


def display_no_results_message() -> None:
    """Display message when no search results are found."""
    st.warning(
        "🔍 No tracklists found for your query. Try adjusting your search terms or check the spelling."
    )
    st.info(
        "💡 **Tips for better results:**\n- Include the DJ/artist name and event name\n- Try different variations of the name\n- Be more specific about the event or venue"
    )
