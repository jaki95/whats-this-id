"""Unit tests for search strategies."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from whats_this_id.core.search.manager import TracklistSearchManager
from whats_this_id.core.search.searcher import SearchResult, SearchStrategy
from whats_this_id.core.search.tracklist1001 import Tracklist1001SearchStrategy


class TestSearchStrategy:
    """Test cases for the base SearchStrategy class."""

    def test_search_strategy_is_abstract(self):
        """Test that SearchStrategy is an abstract base class."""
        with pytest.raises(TypeError):
            SearchStrategy()


class TestSearchResult:
    """Test cases for SearchResult model."""

    def test_search_result_creation(self):
        """Test SearchResult creation with required fields."""
        result = SearchResult(
            link="https://example.com/tracklist",
            title="Test Tracklist",
            snippet="A test tracklist",
        )

        assert result.link == "https://example.com/tracklist"
        assert result.title == "Test Tracklist"
        assert result.snippet == "A test tracklist"

    def test_search_result_with_default_snippet(self):
        """Test SearchResult creation with default snippet."""
        result = SearchResult(
            link="https://example.com/tracklist", title="Test Tracklist"
        )

        assert result.link == "https://example.com/tracklist"
        assert result.title == "Test Tracklist"
        assert result.snippet == ""


class TestTracklist1001SearchStrategy:
    """Test cases for Tracklist1001SearchStrategy."""

    def test_init(self):
        """Test Tracklist1001SearchStrategy initialization."""
        with patch(
            "whats_this_id.core.search.tracklist1001.GoogleHandler"
        ) as mock_google_handler:
            strategy = Tracklist1001SearchStrategy()

            assert strategy.TARGET_SITE == "1001tracklists.com"
            assert strategy.google_handler == mock_google_handler.return_value
            mock_google_handler.assert_called_once()

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    def test_search_success(self, mock_google_handler_class):
        """Test successful search for tracklist."""
        # Setup mock Google handler
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(
            return_value="https://1001tracklists.com/tracklist/123"
        )

        strategy = Tracklist1001SearchStrategy()
        results = strategy.search("test dj set")

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].link == "https://1001tracklists.com/tracklist/123"
        assert results[0].title == "Tracklist: test dj set"
        assert results[0].snippet == "Found tracklist on 1001tracklists.com"

        # Verify Google handler was called correctly
        mock_google_handler.search_for_tracklist_link.assert_called_once_with(
            "1001tracklists.com", "test dj set"
        )

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    def test_search_no_results(self, mock_google_handler_class):
        """Test search when no tracklist is found."""
        # Setup mock Google handler to return None
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(return_value=None)

        strategy = Tracklist1001SearchStrategy()
        results = strategy.search("nonexistent dj set")

        assert len(results) == 0

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    def test_search_exception(self, mock_google_handler_class):
        """Test search when an exception occurs."""
        # Setup mock Google handler to raise exception
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(
            side_effect=Exception("Search error")
        )

        strategy = Tracklist1001SearchStrategy()
        results = strategy.search("test query")

        assert len(results) == 0

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    def test_search_empty_query(self, mock_google_handler_class):
        """Test search with empty query."""
        # Setup mock Google handler
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(return_value=None)

        strategy = Tracklist1001SearchStrategy()
        results = strategy.search("")

        assert len(results) == 0
        mock_google_handler.search_for_tracklist_link.assert_called_once_with(
            "1001tracklists.com", ""
        )

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    def test_search_whitespace_query(self, mock_google_handler_class):
        """Test search with whitespace-only query."""
        # Setup mock Google handler
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(return_value=None)

        strategy = Tracklist1001SearchStrategy()
        results = strategy.search("   ")

        assert len(results) == 0
        mock_google_handler.search_for_tracklist_link.assert_called_once_with(
            "1001tracklists.com", "   "
        )

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    def test_search_with_special_characters(self, mock_google_handler_class):
        """Test search with special characters in query."""
        # Setup mock Google handler
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(
            return_value="https://1001tracklists.com/tracklist/456"
        )

        strategy = Tracklist1001SearchStrategy()
        query = "DJ Set @ Festival 2024 (Live Mix)"
        results = strategy.search(query)

        assert len(results) == 1
        assert results[0].link == "https://1001tracklists.com/tracklist/456"
        assert results[0].title == f"Tracklist: {query}"

        mock_google_handler.search_for_tracklist_link.assert_called_once_with(
            "1001tracklists.com", query
        )

    def test_async_search_method(self):
        """Test the internal _async_search method."""
        with patch("whats_this_id.core.search.tracklist1001.GoogleHandler"):
            strategy = Tracklist1001SearchStrategy()

            # Test that _async_search is a coroutine
            coro = strategy._async_search("test query")
            assert asyncio.iscoroutine(coro)
            # Close the coroutine to avoid the warning
            coro.close()

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    @pytest.mark.asyncio
    async def test_async_search_success(self, mock_google_handler_class):
        """Test successful async search."""
        # Setup mock Google handler
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(
            return_value="https://1001tracklists.com/tracklist/789"
        )

        strategy = Tracklist1001SearchStrategy()
        results = await strategy._async_search("async test query")

        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].link == "https://1001tracklists.com/tracklist/789"
        assert results[0].title == "Tracklist: async test query"
        assert results[0].snippet == "Found tracklist on 1001tracklists.com"

    @patch("whats_this_id.core.search.tracklist1001.GoogleHandler")
    @pytest.mark.asyncio
    async def test_async_search_exception(self, mock_google_handler_class):
        """Test async search when an exception occurs."""
        # Setup mock Google handler to raise exception
        mock_google_handler = Mock()
        mock_google_handler_class.return_value = mock_google_handler
        mock_google_handler.search_for_tracklist_link = AsyncMock(
            side_effect=Exception("Async search error")
        )

        strategy = Tracklist1001SearchStrategy()
        results = await strategy._async_search("test query")

        assert len(results) == 0


class TestTracklistSearchManager:
    """Test cases for TracklistSearchManager."""

    def test_init_default_config(self):
        """Test manager initialization with default config."""
        manager = TracklistSearchManager({})

        assert manager.search_config == {}
        assert "1001tracklists" in manager._strategies

    def test_init_with_config(self):
        """Test manager initialization with custom config."""
        config = {"min_confidence_threshold": 0.8}
        manager = TracklistSearchManager(config)

        assert manager.search_config == config

    def test_search_all_strategies_enabled(self):
        """Test search with all strategies enabled."""
        with patch(
            "whats_this_id.core.search.manager.Tracklist1001SearchStrategy"
        ) as mock_1001_strategy:
            # Setup mock strategy
            mock_1001_instance = Mock()
            mock_1001_instance.search.return_value = [
                SearchResult(
                    link="https://1001tracklists.com/1",
                    title="Tracklist 1",
                    snippet="Snippet 1",
                )
            ]
            mock_1001_strategy.return_value = mock_1001_instance

            manager = TracklistSearchManager({})
            results = manager.search("test query")

            # Should have results from the strategy
            assert len(results) == 1
            assert "1001tracklists.com" in results[0].link

            # Verify strategy was called
            mock_1001_instance.search.assert_called_once_with("test query")

    def test_search_strategy_disabled(self):
        """Test search with a strategy disabled."""
        with patch(
            "whats_this_id.core.search.manager.Tracklist1001SearchStrategy"
        ) as mock_1001_strategy:
            # Setup mock strategy
            mock_1001_instance = Mock()
            mock_1001_instance.search.return_value = [
                SearchResult(
                    link="https://1001tracklists.com/1",
                    title="Tracklist 1",
                    snippet="Snippet 1",
                )
            ]
            mock_1001_strategy.return_value = mock_1001_instance

            # Disable 1001tracklists strategy
            config = {"1001tracklists": False}
            manager = TracklistSearchManager(config)
            results = manager.search("test query")

            # Should have no results since strategy is disabled
            assert len(results) == 0

            # Verify strategy was not called
            mock_1001_instance.search.assert_not_called()

    def test_search_empty_query(self):
        """Test search with empty query."""
        with patch(
            "whats_this_id.core.search.manager.Tracklist1001SearchStrategy"
        ) as mock_1001_strategy:
            # Setup mock strategy to return empty results
            mock_1001_instance = Mock()
            mock_1001_instance.search.return_value = []
            mock_1001_strategy.return_value = mock_1001_instance

            manager = TracklistSearchManager({})
            results = manager.search("")

            assert len(results) == 0

            # Verify strategy was still called
            mock_1001_instance.search.assert_called_once_with("")

    def test_search_strategy_exception(self):
        """Test search when a strategy raises an exception."""
        with patch(
            "whats_this_id.core.search.manager.Tracklist1001SearchStrategy"
        ) as mock_1001_strategy:
            # Setup mock strategy to raise exception
            mock_1001_instance = Mock()
            mock_1001_instance.search.side_effect = Exception("1001tracklists error")
            mock_1001_strategy.return_value = mock_1001_instance

            manager = TracklistSearchManager({})

            # Should raise the exception
            with pytest.raises(Exception, match="1001tracklists error"):
                manager.search("test query")

            # Verify strategy was called
            mock_1001_instance.search.assert_called_once_with("test query")
