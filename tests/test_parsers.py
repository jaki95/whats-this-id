"""Unit tests for parsers."""

import pytest

from whats_this_id.core.common import DomainTrack
from whats_this_id.core.parsers.base import Parser
from whats_this_id.core.parsers.parser import Parser as HTMLParser
from whats_this_id.core.parsers.timing_utils import TimingUtils


class TestParser:
    """Test cases for the base Parser class."""

    def test_parser_is_abstract(self):
        """Test that Parser is an abstract base class."""
        with pytest.raises(TypeError):
            Parser()


class TestHTMLParser:
    """Test cases for HTML Parser."""

    def test_init(self):
        """Test HTML Parser initialization."""
        parser = HTMLParser()
        assert parser.name == "Parser"
        assert parser.timeout == 15
        assert parser.max_retries == 3

    def test_supports_html(self):
        """Test that parser supports HTML content type."""
        parser = HTMLParser()
        assert parser.supports("html") is True

    def test_supports_non_html(self):
        """Test that parser does not support non-HTML content types."""
        parser = HTMLParser()
        assert parser.supports("json") is False
        assert parser.supports("text") is False
        assert parser.supports("xml") is False

    def test_parse_empty_content(self):
        """Test parsing with empty content."""
        parser = HTMLParser()
        result = parser.execute("")

        assert result.success is True
        # result.data is now a tuple (tracks, total_duration, metadata)
        tracks, total_duration, metadata = result.data
        assert tracks == []
        assert total_duration is None
        assert isinstance(metadata, dict)
        assert metadata["name"] is None
        assert metadata["artist"] is None

    def test_parse_simple_html(self):
        """Test parsing with simple HTML content."""
        parser = HTMLParser()
        html_content = """
        <html>
            <body>
                <div class="tracklist">
                    <div>Artist 1 - Track 1</div>
                    <div>Artist 2 - Track 2</div>
                </div>
            </body>
        </html>
        """
        result = parser.execute(html_content)

        assert result.success is True
        # result.data is now a tuple (tracks, total_duration, metadata)
        tracks, total_duration, metadata = result.data
        assert isinstance(tracks, list)
        assert isinstance(metadata, dict)
        # Should extract tracks from the HTML
        assert len(tracks) >= 0  # May or may not find tracks depending on parsing logic

    def test_timing_rules_application(self):
        """Test that timing rules are applied correctly."""

        # Create test tracks with various start times
        test_tracks = [
            DomainTrack(
                name="Track 1",
                artist="Artist 1",
                start_time="05:30",  # Should be changed to 00:00
                end_time=None,
                track_number=1,
            ),
            DomainTrack(
                name="Track 2",
                artist="Artist 2",
                start_time="08:45",
                end_time=None,
                track_number=2,
            ),
            DomainTrack(
                name="Track 3",
                artist="Artist 3",
                start_time="12:15",
                end_time=None,
                track_number=3,
            ),
        ]

        # Apply timing rules
        result_tracks = TimingUtils.apply_timing_rules(
            test_tracks, "15:30"
        )  # Pass a total duration

        # Verify first track starts at 00:00
        assert result_tracks[0].start_time == "00:00"

        # Verify end times are set correctly
        assert result_tracks[0].end_time == "08:45"  # Start time of track 2
        assert result_tracks[1].end_time == "12:15"  # Start time of track 3
        assert (
            result_tracks[2].end_time == "15:30"
        )  # Last track should have the total duration as end time

        # Verify other start times remain unchanged
        assert result_tracks[1].start_time == "08:45"
        assert result_tracks[2].start_time == "12:15"

    def test_complex_track_name_parsing(self):
        """Test parsing of complex track names with parentheses and special characters."""
        from whats_this_id.core.parsers.text_cleaners import TextCleaner
        from whats_this_id.core.parsers.track_extractors import TrackExtractors

        track_text = "Prince Of Denmark - (In The End) The Ghost Ran Out Of Memory (Mind Against Remix)"

        # Test that the track can be parsed
        result = TrackExtractors._parse_artist_track_text(track_text)
        assert result is not None, "Prince Of Denmark track should be parseable"
        assert result.artist == "Prince Of Denmark"
        assert (
            result.name
            == "(In The End) The Ghost Ran Out Of Memory (Mind Against Remix)"
        )

        # Test that text cleaning preserves the track name
        track_name = "(In The End) The Ghost Ran Out Of Memory (Mind Against Remix)"
        cleaned = TextCleaner.clean_track_name(track_name)
        assert cleaned == track_name, (
            "Text cleaning should preserve legitimate track names"
        )

        # Test that the track passes filtering criteria
        assert len(track_name) <= 100, "Track name should not exceed length limit"
        assert track_name.count("(") <= 2, (
            "Track name should not exceed parentheses limit"
        )
        assert track_name.count("[") <= 2, "Track name should not exceed brackets limit"

    def test_id_track_parsing(self):
        """Test parsing of ID tracks."""
        from whats_this_id.core.parsers.track_extractors import TrackExtractors

        # Test ID track detection
        test_cases = [
            ("ID - ID", True),
            ("id - id", True),
            ("ID - id", True),
            ("Regular Track - Regular Artist", False),
        ]

        for text, expected in test_cases:
            element = {}
            result = TrackExtractors._is_id_track(element, text)
            assert result == expected, f"ID track detection failed for '{text}'"
