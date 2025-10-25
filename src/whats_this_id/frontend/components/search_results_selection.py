"""Component for displaying multiple search results and allowing user selection."""

import streamlit as st

from whats_this_id.frontend.state import select_search_result


def render_search_results_selection():
    """Render the search results selection component."""
    # Only show selection if we have results but no selection yet
    if not st.session_state.search_results:
        return

    # If a result is already selected, show a way to go back to selection
    if st.session_state.selected_result_index is not None:
        if st.button("Go Back", key="clear_selection"):
            st.session_state.selected_result_index = None
            st.session_state.tracklist = None
            st.session_state.dj_set_url = None
            st.rerun()
        return

    st.write(
        f"Found {len(st.session_state.search_results)} tracklist(s). Select one to continue:"
    )

    # Display each search result
    for i, search_result in enumerate(st.session_state.search_results):
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.subheader(f"{i + 1}. {search_result.title}")

            with col2:
                button_key = f"select_result_{i}_{hash(search_result.title)}"
                if st.button("Select", key=button_key, type="primary"):
                    select_search_result(i)
                    # Force a rerun by updating a session state variable
                    st.session_state.force_rerun = not st.session_state.get(
                        "force_rerun", False
                    )
                    st.rerun()

            st.divider()
