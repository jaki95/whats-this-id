"""Frontend components for the What's This ID application."""

from .download_section import render_download_section
from .processing_controls import render_processing_controls
from .results import render_results_section
from .search import render_search_section
from .tracklist_display import render_tracklist_display

__all__ = [
    "render_search_section",
    "render_results_section",
    "render_tracklist_display",
    "render_processing_controls",
    "render_download_section",
]
