import pandas as pd
import streamlit as st

from whats_this_id.agents import TracklistSearchCrew
from whats_this_id.core.models.tracklist import Tracklist

# Page configuration
st.set_page_config(
    page_title="What's This ID?",
    page_icon="💿",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application function."""
    # Header
    st.title("💿 What's This ID?")
    st.markdown(
        "Find the IDs of a DJ set using natural language queries with AI-powered multi-agent orchestration"
    )

    # Initialize session state
    if "query_text" not in st.session_state:
        st.session_state.query_text = ""

    st.header("🔍 Search Tracklists")

    # Search input
    query = st.text_area(
        "Enter your tracklist search query:",
        value=st.session_state.query_text,
        placeholder="e.g., 'Mind Against - Afterlife Awakenings'",
        height=100,
        key="query_input",
    )

    # Update session state when text area changes
    if query != st.session_state.query_text:
        st.session_state.query_text = query

    # Search button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button(
            "🔍 Search Tracklists", type="primary", use_container_width=True
        )

    # Handle search
    if search_button:
        if st.session_state.query_text.strip():
            with st.spinner("🤖 AI agents are searching for tracklists..."):
                inputs = {"dj_set": st.session_state.query_text.strip()}
                result = TracklistSearchCrew().crew().kickoff(inputs=inputs)
                tracklist: Tracklist = result.pydantic
                st.header(f"🎵 {tracklist.name}")
                st.markdown(f"**Artist:** {tracklist.artist}")
                st.markdown(f"**Year:** {tracklist.year}")
                st.markdown(f"**Genre:** {tracklist.genre}")
                st.markdown(f"**Tracks:**")
                st.markdown("---")
                for i, track in enumerate(tracklist.tracks):
                    st.markdown(f"**{i+1}. {track.name}** - {track.artist}")
                    st.markdown(f"**Start Time:** {track.start_time}")
                    st.markdown(f"**End Time:** {track.end_time}")
                    st.markdown("---")
        else:
            st.warning("⚠️ Please enter a search query.")


if __name__ == "__main__":
    main()
