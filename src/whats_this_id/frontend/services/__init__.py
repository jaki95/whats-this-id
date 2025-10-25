"""Frontend services for the What's This ID application."""

# Import core services for direct access if needed
from whats_this_id.core.services import SearchService, search_service

from .djset_processor import (
    FrontendDJSetProcessorService,
    display_api_error,
    djset_processor_service,
)

__all__ = [
    "FrontendDJSetProcessorService",
    "djset_processor_service",
    "display_api_error",
    "SearchService",
    "search_service",
]
