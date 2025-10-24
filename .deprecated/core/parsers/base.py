"""
Base parser classes.
"""

from abc import ABC, abstractmethod
from typing import Any


class Parser(ABC):
    """Abstract base class for content parsers."""

    @abstractmethod
    def parse(self, content: str) -> tuple[list[Any], float]:
        """Parse content and return tracks with confidence score."""
        pass

    @abstractmethod
    def supports(self, content_type: str) -> bool:
        """Check if this parser supports the given content type."""
        pass
