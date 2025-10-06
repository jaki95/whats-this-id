"""Pytest configuration and fixtures."""

from unittest.mock import Mock

import pytest

from whats_this_id.core.common import DomainTrack
from whats_this_id.core.search.searcher import SearchResult


@pytest.fixture
def mock_search_result():
    """Create a mock search result."""
    return SearchResult(
        url="https://example.com/tracklist",
        title="Test Tracklist",
        snippet="A test tracklist for unit testing",
    )


@pytest.fixture
def mock_domain_track():
    """Create a mock domain track."""
    track = Mock(spec=DomainTrack)
    track.title = "Test Track"
    track.name = "Test Track"  # Add name attribute for compatibility
    track.artist = "Test Artist"
    return track


@pytest.fixture
def mock_domain_tracks():
    """Create a list of mock domain tracks."""
    tracks = []
    for i in range(3):
        track = Mock(spec=DomainTrack)
        track.title = f"Test Track {i + 1}"
        track.name = f"Test Track {i + 1}"  # Add name attribute for compatibility
        track.artist = f"Test Artist {i + 1}"
        track.start_time = f"0{i}:00" if i < 10 else f"{i}:00"
        track.end_time = None
        track.track_number = i + 1
        tracks.append(track)
    return tracks


@pytest.fixture
def mock_searcher():
    """Create a mock searcher."""
    searcher = Mock()
    searcher.name = "MockSearcher"
    searcher.search.return_value = []
    return searcher


@pytest.fixture
def mock_fetcher():
    """Create a mock fetcher."""
    fetcher = Mock()
    fetcher.name = "MockFetcher"
    fetcher.content_type = "html"
    fetcher.fetch.return_value = "<html>Mock content</html>"
    return fetcher


@pytest.fixture
def mock_parser():
    """Create a mock parser."""
    parser = Mock()
    parser.supports.return_value = True
    parser.parse.return_value = ([], 0.8)
    return parser


@pytest.fixture
def search_config():
    """Create a test search configuration."""
    return {"min_confidence_threshold": 0.7, "max_results": 10}
