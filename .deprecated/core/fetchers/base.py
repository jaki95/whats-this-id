"""
Base fetcher classes.
"""

from abc import ABC, abstractmethod


class Fetcher(ABC):
    """Abstract base class for content fetchers."""

    @abstractmethod
    def fetch(self, url: str) -> str:
        """Fetch content from the given URL."""
        pass

    @abstractmethod
    def supports(self, content_type: str) -> bool:
        """Check if this fetcher supports the given content type."""
        pass
