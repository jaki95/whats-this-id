"""Unit tests for fetchers."""

import pytest

from whats_this_id.core.fetchers.base import Fetcher
from whats_this_id.core.fetchers.fetcher import Fetcher as HTMLFetcher


class TestFetcher:
    """Test cases for the base Fetcher class."""

    def test_fetcher_is_abstract(self):
        """Test that Fetcher is an abstract base class."""
        with pytest.raises(TypeError):
            Fetcher()


class TestHTMLFetcher:
    """Test cases for HTML Fetcher."""

    def test_init(self):
        """Test HTML Fetcher initialization."""
        fetcher = HTMLFetcher()
        assert fetcher.name == "html"
        assert fetcher.content_type == "html"
        assert fetcher.timeout == 30
        assert fetcher.max_retries == 1

    def test_fetch_empty_url(self):
        """Test fetch with empty URL."""
        fetcher = HTMLFetcher()
        result = fetcher.fetch("")

        # Should return empty string for invalid URLs
        assert result == ""

    def test_fetch_invalid_url(self):
        """Test fetch with invalid URL."""
        fetcher = HTMLFetcher()
        result = fetcher.fetch("invalid-url")

        # Should handle gracefully and return empty string
        assert result == ""
