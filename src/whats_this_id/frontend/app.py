"""Main Streamlit application for What's This ID."""

import streamlit as st

from whats_this_id.frontend.components import (
    render_results_section,
    render_search_section,
)
from whats_this_id.frontend.components.search_results_selection import (
    render_search_results_selection,
)
from whats_this_id.frontend.config import AppConfig, configure_streamlit_page
from whats_this_id.frontend.state import initialize_session_state


def render_app_header():
    """Render the application header and description."""
    st.title(AppConfig.APP_TITLE)
    st.markdown(AppConfig.APP_DESCRIPTION)


def main():
    configure_streamlit_page()

    initialize_session_state()

    render_app_header()
    render_search_section()
    render_search_results_selection()
    render_results_section()


if __name__ == "__main__":
    main()
