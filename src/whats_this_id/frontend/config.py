"""Configuration settings for the What's This ID frontend application."""

import streamlit as st
from typing import Dict, Any


class AppConfig:
    """Application configuration constants and settings."""
    
    # App metadata
    APP_TITLE = "What's This ID?"
    APP_ICON = "💿"
    APP_DESCRIPTION = (
        "Find the IDs of a DJ set using natural language queries "
        "with AI-powered multi-agent orchestration"
    )
    
    # Page configuration
    PAGE_CONFIG = {
        "page_title": APP_TITLE,
        "page_icon": APP_ICON,
        "layout": "wide",
        "initial_sidebar_state": "expanded",
    }
    
    # UI Constants
    SEARCH_PLACEHOLDER = "Enter your tracklist search query:"
    SEARCH_BUTTON_TEXT = "Search Tracklists"
    SEARCH_SPINNER_TEXT = "🤖 AI agents are searching for tracklists and SoundCloud..."
    
    # Layout
    TRACKLIST_RESULTS_COLUMNS = [2, 1]  # [tracklist_display, processing_section]
    SEARCH_BUTTON_COLUMNS = [2, 1, 2]   # [empty, button, empty]
    
    # Processing
    DEFAULT_FILE_EXTENSION = "m4a"
    DEFAULT_MAX_CONCURRENT_TASKS = 4
    
    # API
    DEFAULT_API_BASE_URL = "http://localhost:8000"


def configure_streamlit_page():
    """Configure the Streamlit page with app settings."""
    st.set_page_config(**AppConfig.PAGE_CONFIG) 