"""Unit tests for TracklistSearchManager."""

from datetime import datetime
from unittest.mock import Mock, patch

from dj_set_downloader.models.domain_track import DomainTrack

from whats_this_id.core.common import SearchRun, StepLog
from whats_this_id.core.manager import TracklistManager
from whats_this_id.core.search.searcher import SearchResult


class TestTracklistManager:
    """Test cases for TracklistManager."""

    def test_init_default_config(self):
        """Test manager initialization with default config."""
        manager = TracklistManager()

        assert manager.config is not None
        assert manager.searcher is not None
        assert manager.fetcher is not None
        assert manager.parser is not None
        assert manager.min_confidence_threshold == 0.5

    def test_init_with_config(self, search_config):
        """Test manager initialization with custom config."""
        manager = TracklistManager(search_config)

        # Config should contain the custom values merged with defaults
        assert manager.config["min_confidence_threshold"] == 0.7
        assert manager.min_confidence_threshold == 0.7

    def test_run_empty_query(self):
        """Test run method with empty query."""
        manager = TracklistManager()
        result = manager.run("")

        assert isinstance(result, SearchRun)
        assert result.query == ""
        assert result.success is False
        assert len(result.steps) == 1
        assert result.steps[0].step_name == "Validation"
        assert result.steps[0].status == "error"
        assert "Query cannot be empty" in result.steps[0].error

    def test_run_whitespace_query(self):
        """Test run method with whitespace-only query."""
        manager = TracklistManager()
        result = manager.run("   ")

        assert isinstance(result, SearchRun)
        assert result.query == "   "
        assert result.success is False
        assert len(result.steps) == 1
        assert result.steps[0].step_name == "Validation"
        assert result.steps[0].status == "error"

    @patch("whats_this_id.core.manager.logger")
    def test_run_successful_search(
        self, mock_logger, mock_searcher, mock_fetcher, mock_parser, mock_domain_tracks
    ):
        """Test successful search run."""
        # Setup mocks
        mock_searcher.search_tracklist1001.return_value = [
            SearchResult(url="https://test.com", title="Test", snippet="Test")
        ]
        mock_parser.parse.return_value = (
            mock_domain_tracks,
            0.9,
            None,
            {"name": "Test Set", "artist": "Test Artist"},
        )
        mock_parser._apply_timing_rules.return_value = mock_domain_tracks

        manager = TracklistManager()
        manager.searcher = mock_searcher
        manager.fetcher = mock_fetcher
        manager.parser = mock_parser

        result = manager.run("test query")

        assert isinstance(result, SearchRun)
        assert result.query == "test query"
        assert result.success is True
        assert len(result.final_tracklist.tracks) == 3
        assert result.total_duration_ms is not None

        # Check that search was called
        mock_searcher.search_tracklist1001.assert_called_once_with("test query")
        mock_fetcher.fetch.assert_called_once()
        mock_parser.parse.assert_called_once()

    def test_run_search_error(self, mock_searcher):
        """Test run method when search fails."""
        mock_searcher.search_tracklist1001.side_effect = Exception("Search failed")

        manager = TracklistManager()
        manager.searcher = mock_searcher

        result = manager.run("test query")

        assert isinstance(result, SearchRun)
        assert result.success is False
        assert len(result.steps) >= 1

        # Check for error step
        error_steps = [step for step in result.steps if step.status == "error"]
        assert len(error_steps) > 0

    def test_run_parse_error(self, mock_searcher, mock_fetcher, mock_parser):
        """Test run method when parsing fails."""
        mock_searcher.search_tracklist1001.return_value = [
            SearchResult(url="https://test.com", title="Test", snippet="Test")
        ]
        mock_parser.parse.side_effect = Exception("Parse failed")

        manager = TracklistManager()
        manager.searcher = mock_searcher
        manager.fetcher = mock_fetcher
        manager.parser = mock_parser

        result = manager.run("test query")

        assert isinstance(result, SearchRun)
        assert result.success is False
        assert (
            result.final_tracklist.tracks is None
            or len(result.final_tracklist.tracks) == 0
        )

    def test_run_low_confidence_filtering(
        self, mock_searcher, mock_fetcher, mock_parser
    ):
        """Test that low confidence results are filtered out."""
        mock_searcher.search_tracklist1001.return_value = [
            SearchResult(url="https://test.com", title="Test", snippet="Test")
        ]
        mock_parser.parse.return_value = ([], 0.3)  # Low confidence

        manager = TracklistManager({"min_confidence_threshold": 0.7})
        manager.searcher = mock_searcher
        manager.fetcher = mock_fetcher
        manager.parser = mock_parser

        result = manager.run("test query")

        assert isinstance(result, SearchRun)
        assert result.success is False
        assert (
            result.final_tracklist.tracks is None
            or len(result.final_tracklist.tracks) == 0
        )

    def test_search_tracklists_success(self, mock_searcher):
        """Test _search_tracklists method with successful search."""
        mock_searcher.search_tracklist1001.return_value = [
            SearchResult(url="https://test.com", title="Test", snippet="Test")
        ]

        manager = TracklistManager()
        manager.searcher = mock_searcher

        run = SearchRun(query="test")
        results = manager._search_tracklists("test query", run)

        assert len(results) == 1
        assert results[0].url == "https://test.com"
        assert len(run.steps) == 1
        assert run.steps[0].step_name == "Search"
        assert run.steps[0].status == "success"

    def test_search_tracklists_error(self, mock_searcher):
        """Test _search_tracklists method with search error."""
        mock_searcher.search_tracklist1001.side_effect = Exception("Search failed")

        manager = TracklistManager()
        manager.searcher = mock_searcher

        run = SearchRun(query="test")
        results = manager._search_tracklists("test query", run)

        assert len(results) == 0
        assert len(run.steps) == 1
        assert run.steps[0].step_name == "Search"
        assert run.steps[0].status == "error"

    def test_fetch_and_parse_success(
        self, mock_fetcher, mock_parser, mock_domain_tracks
    ):
        """Test _fetch_and_parse method with successful parsing."""
        mock_parser.parse.return_value = (
            mock_domain_tracks,
            0.9,
            None,
            {"name": "Test Set", "artist": "Test Artist"},
        )

        manager = TracklistManager()
        manager.fetcher = mock_fetcher
        manager.parser = mock_parser

        results = [SearchResult(url="https://test.com", title="Test", snippet="Test")]
        run = SearchRun(query="test")

        parsed_tracklists = manager._fetch_and_parse(results, run)

        assert len(parsed_tracklists) == 1
        assert len(parsed_tracklists[0][0]) == 3  # 3 tracks
        assert parsed_tracklists[0][1] == 0.9  # confidence
        assert parsed_tracklists[0][2] is None  # duration
        assert parsed_tracklists[0][3]["name"] == "Test Set"  # metadata
        assert len(run.steps) == 1
        assert run.steps[0].step_name == "Parse"

    def test_fetch_and_parse_no_parser(self, mock_fetcher):
        """Test _fetch_and_parse method when parser doesn't support content type."""
        # Create a parser that doesn't support HTML
        mock_parser = Mock()
        mock_parser.supports.return_value = False

        manager = TracklistManager()
        manager.fetcher = mock_fetcher
        manager.parser = mock_parser

        results = [SearchResult(url="https://test.com", title="Test", snippet="Test")]
        run = SearchRun(query="test")

        parsed_tracklists = manager._fetch_and_parse(results, run)

        assert len(parsed_tracklists) == 0

    def test_parser_supports_html(self, mock_parser):
        """Test that parser supports HTML content type."""
        mock_parser.supports.return_value = True

        manager = TracklistManager()

        # Test that the parser supports HTML
        assert manager.parser.supports("html") is True

    def test_merge_results_empty(self):
        """Test _merge_results method with empty tracklists."""
        manager = TracklistManager()
        run = SearchRun(query="test")

        manager._merge_results([], run)

        assert (
            run.final_tracklist.tracks is None or len(run.final_tracklist.tracks) == 0
        )
        assert len(run.steps) == 1
        assert run.steps[0].step_name == "Aggregation"
        assert run.steps[0].status == "no_results"

    def test_merge_results_with_deduplication(self, mock_domain_tracks):
        """Test _merge_results method with deduplication."""
        # Create duplicate tracks
        track1 = Mock(spec=DomainTrack)
        track1.title = "Same Track"
        track1.name = "Same Track"  # Add name attribute for compatibility
        track1.start_time = "00:00"
        track1.end_time = None
        track2 = Mock(spec=DomainTrack)
        track2.title = "Same Track"  # Duplicate
        track2.name = "Same Track"  # Add name attribute for compatibility
        track2.start_time = "05:00"
        track2.end_time = None
        track3 = Mock(spec=DomainTrack)
        track3.title = "Different Track"
        track3.name = "Different Track"  # Add name attribute for compatibility
        track3.start_time = "10:00"
        track3.end_time = None

        parsed_tracklists = [
            ([track1, track2], 0.8, None, {"name": "Set 1", "artist": "Artist 1"}),
            ([track3], 0.9, None, {"name": "Set 2", "artist": "Artist 2"}),
        ]

        manager = TracklistManager()
        run = SearchRun(query="test")

        manager._merge_results(parsed_tracklists, run)

        assert len(run.final_tracklist.tracks) == 2  # Duplicate removed
        # Check that both tracks are present (order may vary due to sorting logic)
        track_titles = [track.title for track in run.final_tracklist.tracks]
        assert "Same Track" in track_titles
        assert "Different Track" in track_titles
        assert len(run.steps) == 1
        assert run.steps[0].step_name == "Aggregation"
        assert run.steps[0].status == "success"

    def test_merge_results_case_insensitive_deduplication(self):
        """Test that deduplication is case-insensitive."""
        track1 = Mock(spec=DomainTrack)
        track1.title = "Same Track"
        track1.name = "Same Track"  # Add name attribute for compatibility
        track1.start_time = "00:00"
        track1.end_time = None
        track2 = Mock(spec=DomainTrack)
        track2.title = "SAME TRACK"  # Different case
        track2.name = "SAME TRACK"  # Add name attribute for compatibility
        track2.start_time = "05:00"
        track2.end_time = None

        parsed_tracklists = [
            ([track1, track2], 0.8, None, {"name": "Test Set", "artist": "Test Artist"})
        ]

        manager = TracklistManager()
        run = SearchRun(query="test")

        manager._merge_results(parsed_tracklists, run)

        assert (
            len(run.final_tracklist.tracks) == 1
        )  # Duplicate removed despite case difference

    def test_log_step_helper(self):
        """Test log_step helper function."""
        from whats_this_id.core.common import log_step

        run = SearchRun(query="test")

        log_step(
            run,
            "TestStep",
            "TestSource",
            "success",
            details="Test details",
            found_tracks=5,
            confidence=0.8,
            link="https://test.com",
            duration_ms=100.0,
        )

        assert len(run.steps) == 1
        step = run.steps[0]
        assert step.step_name == "TestStep"
        assert step.source == "TestSource"
        assert step.status == "success"
        assert step.details == "Test details"
        assert step.found_tracks == 5
        assert step.confidence == 0.8
        assert step.link == "https://test.com"
        assert step.duration_ms == 100.0

    def test_run_timing(self, mock_searcher, mock_fetcher, mock_parser):
        """Test that run method records timing information."""
        mock_searcher.search_tracklist1001.return_value = []

        manager = TracklistManager()
        manager.searcher = mock_searcher
        manager.fetcher = mock_fetcher
        manager.parser = mock_parser

        result = manager.run("test query")

        assert result.total_duration_ms is not None
        assert result.total_duration_ms >= 0

    def test_run_exception_handling(self, mock_searcher):
        """Test that run method handles unexpected exceptions."""
        mock_searcher.search_tracklist1001.side_effect = Exception("Unexpected error")

        manager = TracklistManager()
        manager.searcher = mock_searcher

        result = manager.run("test query")

        assert isinstance(result, SearchRun)
        assert result.success is False
        # Should have both search error and manager error steps
        error_steps = [step for step in result.steps if step.status == "error"]
        assert len(error_steps) >= 1


class TestSearchRun:
    """Test cases for SearchRun model."""

    def test_search_run_creation(self):
        """Test SearchRun model creation."""
        run = SearchRun(query="test query")

        assert run.query == "test query"
        assert run.run_id is not None
        assert isinstance(run.timestamp, datetime)
        assert run.steps == []
        assert run.final_tracklist.tracks is None or run.final_tracklist.tracks == []
        assert run.total_duration_ms is None
        assert run.success is False

    def test_search_run_with_steps(self):
        """Test SearchRun with steps."""
        step = StepLog(
            step_name="Test",
            source="TestSource",
            status="success",
            details="Test details",
        )

        run = SearchRun(query="test", steps=[step])

        assert len(run.steps) == 1
        assert run.steps[0].step_name == "Test"


class TestStepLog:
    """Test cases for StepLog model."""

    def test_step_log_creation(self):
        """Test StepLog model creation."""
        step = StepLog(step_name="TestStep", source="TestSource", status="success")

        assert step.step_name == "TestStep"
        assert step.source == "TestSource"
        assert step.status == "success"
        assert step.details == ""
        assert step.confidence is None
        assert step.found_tracks is None
        assert step.link is None
        assert step.error is None
        assert step.duration_ms is None

    def test_step_log_with_all_fields(self):
        """Test StepLog with all fields populated."""
        step = StepLog(
            step_name="TestStep",
            source="TestSource",
            status="success",
            details="Test details",
            confidence=0.8,
            found_tracks=5,
            link="https://test.com",
            error="Test error",
            duration_ms=100.0,
        )

        assert step.step_name == "TestStep"
        assert step.source == "TestSource"
        assert step.status == "success"
        assert step.details == "Test details"
        assert step.confidence == 0.8
        assert step.found_tracks == 5
        assert step.link == "https://test.com"
        assert step.error == "Test error"
        assert step.duration_ms == 100.0
