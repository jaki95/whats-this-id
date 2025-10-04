"""Unit tests for fetchers."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from whats_this_id.core.fetchers.base import Fetcher
from whats_this_id.core.fetchers.html_fetcher import HTMLFetcher


class TestFetcher:
    """Test cases for the base Fetcher class."""

    def test_fetcher_is_abstract(self):
        """Test that Fetcher is an abstract base class."""
        with pytest.raises(TypeError):
            Fetcher()


class TestHTMLFetcher:
    """Test cases for HTMLFetcher."""

    def test_init(self):
        """Test HTMLFetcher initialization."""
        fetcher = HTMLFetcher()

        assert fetcher.name == "html"
        assert fetcher.content_type == "html"

    @patch("whats_this_id.core.fetchers.html_fetcher.AsyncWebCrawler")
    @patch("whats_this_id.core.fetchers.html_fetcher.browser_config")
    @patch("whats_this_id.core.fetchers.html_fetcher.crawler_config")
    def test_fetch_success(
        self, mock_crawler_config, mock_browser_config, mock_crawler_class
    ):
        """Test successful HTML fetch."""
        # Setup mock crawler
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler

        # Mock successful result
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = "<html><body>Test content</body></html>"
        mock_crawler.arun.return_value = mock_result

        fetcher = HTMLFetcher()
        result = fetcher.fetch("https://example.com")

        assert result == "<html><body>Test content</body></html>"
        mock_crawler.arun.assert_called_once_with(
            url="https://example.com", config=mock_crawler_config
        )

    @patch("whats_this_id.core.fetchers.html_fetcher.AsyncWebCrawler")
    @patch("whats_this_id.core.fetchers.html_fetcher.browser_config")
    @patch("whats_this_id.core.fetchers.html_fetcher.crawler_config")
    def test_fetch_failure(
        self, mock_crawler_config, mock_browser_config, mock_crawler_class
    ):
        """Test HTML fetch when crawler fails."""
        # Setup mock crawler
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler

        # Mock failed result
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Network error"
        mock_crawler.arun.return_value = mock_result

        fetcher = HTMLFetcher()
        result = fetcher.fetch("https://example.com")

        assert result == ""

    @patch("whats_this_id.core.fetchers.html_fetcher.AsyncWebCrawler")
    @patch("whats_this_id.core.fetchers.html_fetcher.browser_config")
    @patch("whats_this_id.core.fetchers.html_fetcher.crawler_config")
    def test_fetch_exception(
        self, mock_crawler_config, mock_browser_config, mock_crawler_class
    ):
        """Test HTML fetch when an exception occurs."""
        # Setup mock crawler to raise exception
        mock_crawler_class.side_effect = Exception("Crawler error")

        fetcher = HTMLFetcher()
        result = fetcher.fetch("https://example.com")

        assert result == ""

    @patch("whats_this_id.core.fetchers.html_fetcher.AsyncWebCrawler")
    @patch("whats_this_id.core.fetchers.html_fetcher.browser_config")
    @patch("whats_this_id.core.fetchers.html_fetcher.crawler_config")
    def test_fetch_empty_url(
        self, mock_crawler_config, mock_browser_config, mock_crawler_class
    ):
        """Test HTML fetch with empty URL."""
        # Setup mock crawler
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler

        # Mock successful result
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = "<html><body>Empty URL content</body></html>"
        mock_crawler.arun.return_value = mock_result

        fetcher = HTMLFetcher()
        result = fetcher.fetch("")

        assert result == "<html><body>Empty URL content</body></html>"
        mock_crawler.arun.assert_called_once_with(url="", config=mock_crawler_config)

    @patch("whats_this_id.core.fetchers.html_fetcher.AsyncWebCrawler")
    @patch("whats_this_id.core.fetchers.html_fetcher.browser_config")
    @patch("whats_this_id.core.fetchers.html_fetcher.crawler_config")
    def test_fetch_uses_correct_config(
        self, mock_crawler_config, mock_browser_config, mock_crawler_class
    ):
        """Test that HTMLFetcher uses the correct browser and crawler config."""
        # Setup mock crawler
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler

        # Mock successful result
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = "<html>Test</html>"
        mock_crawler.arun.return_value = mock_result

        fetcher = HTMLFetcher()
        fetcher.fetch("https://example.com")

        # Verify AsyncWebCrawler was called with browser_config
        mock_crawler_class.assert_called_once_with(config=mock_browser_config)

    def test_async_fetch_method(self):
        """Test the internal _async_fetch method."""
        fetcher = HTMLFetcher()

        # Test that _async_fetch is a coroutine
        coro = fetcher._async_fetch("https://example.com")
        assert asyncio.iscoroutine(coro)
        # Close the coroutine to avoid the warning
        coro.close()

    @patch("whats_this_id.core.fetchers.html_fetcher.AsyncWebCrawler")
    @patch("whats_this_id.core.fetchers.html_fetcher.browser_config")
    @patch("whats_this_id.core.fetchers.html_fetcher.crawler_config")
    @pytest.mark.asyncio
    async def test_async_fetch_success(
        self, mock_crawler_config, mock_browser_config, mock_crawler_class
    ):
        """Test successful async fetch."""
        # Setup mock crawler
        mock_crawler = AsyncMock()
        mock_crawler_class.return_value.__aenter__.return_value = mock_crawler

        # Mock successful result
        mock_result = Mock()
        mock_result.success = True
        mock_result.html = "<html><body>Async test content</body></html>"
        mock_crawler.arun.return_value = mock_result

        fetcher = HTMLFetcher()
        result = await fetcher._async_fetch("https://example.com")

        assert result == "<html><body>Async test content</body></html>"
        mock_crawler.arun.assert_called_once_with(
            url="https://example.com", config=mock_crawler_config
        )

    @patch("whats_this_id.core.fetchers.html_fetcher.AsyncWebCrawler")
    @patch("whats_this_id.core.fetchers.html_fetcher.browser_config")
    @patch("whats_this_id.core.fetchers.html_fetcher.crawler_config")
    @pytest.mark.asyncio
    async def test_async_fetch_exception(
        self, mock_crawler_config, mock_browser_config, mock_crawler_class
    ):
        """Test async fetch when an exception occurs."""
        # Setup mock crawler to raise exception
        mock_crawler_class.side_effect = Exception("Async crawler error")

        fetcher = HTMLFetcher()
        result = await fetcher._async_fetch("https://example.com")

        assert result == ""
