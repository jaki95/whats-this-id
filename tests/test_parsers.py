"""Unit tests for parsers."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from dj_set_downloader.models.domain_track import DomainTrack
from dj_set_downloader.models.domain_tracklist import DomainTracklist

from whats_this_id.core.parsers.base import Parser
from whats_this_id.core.parsers.llm_parser import LLMTracklistParser


class TestParser:
    """Test cases for the base Parser class."""

    def test_parser_is_abstract(self):
        """Test that Parser is an abstract base class."""
        with pytest.raises(TypeError):
            Parser()


class TestLLMTracklistParser:
    """Test cases for LLMTracklistParser."""

    def test_init_default_model(self):
        """Test LLMTracklistParser initialization with default model."""
        with patch("whats_this_id.core.parsers.llm_parser.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            parser = LLMTracklistParser()

            assert parser.model == "gpt-4o-mini"
            assert parser.client == mock_client
            mock_openai.assert_called_once()

    def test_init_custom_model(self):
        """Test LLMTracklistParser initialization with custom model."""
        with patch("whats_this_id.core.parsers.llm_parser.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            parser = LLMTracklistParser(model="gpt-4")

            assert parser.model == "gpt-4"
            assert parser.client == mock_client
            mock_openai.assert_called_once()

    def test_supports_html(self):
        """Test that parser supports HTML content type."""
        with patch("whats_this_id.core.parsers.llm_parser.OpenAI"):
            parser = LLMTracklistParser()

            assert parser.supports("html") is True

    def test_supports_non_html(self):
        """Test that parser does not support non-HTML content types."""
        with patch("whats_this_id.core.parsers.llm_parser.OpenAI"):
            parser = LLMTracklistParser()

            assert parser.supports("json") is False
            assert parser.supports("text") is False
            assert parser.supports("xml") is False

    @patch("whats_this_id.core.parsers.llm_parser.OpenAI")
    def test_parse_success(self, mock_openai):
        """Test successful parsing of HTML content."""
        # Setup mock client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        # Create mock domain tracks
        mock_track1 = Mock(spec=DomainTrack)
        mock_track1.title = "Track 1"
        mock_track1.artist = "Artist 1"

        mock_track2 = Mock(spec=DomainTrack)
        mock_track2.title = "Track 2"
        mock_track2.artist = "Artist 2"

        mock_tracklist = Mock(spec=DomainTracklist)
        mock_tracklist.tracks = [mock_track1, mock_track2]

        # Setup mock response
        mock_response = Mock()
        mock_response.output_parsed = mock_tracklist
        mock_client.responses.parse.return_value = mock_response

        parser = LLMTracklistParser()
        result = parser.parse("<html>Test tracklist content</html>")

        assert result == mock_tracklist
        mock_client.responses.parse.assert_called_once_with(
            model="gpt-4o-mini",
            text_format=DomainTracklist,
            input=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that parses tracklists from HTML content.",
                },
                {"role": "user", "content": "<html>Test tracklist content</html>"},
            ],
        )

    @patch("whats_this_id.core.parsers.llm_parser.OpenAI")
    def test_parse_with_custom_model(self, mock_openai):
        """Test parsing with custom model."""
        # Setup mock client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_tracklist = Mock(spec=DomainTracklist)
        mock_tracklist.tracks = []

        mock_response = Mock()
        mock_response.output_parsed = mock_tracklist
        mock_client.responses.parse.return_value = mock_response

        parser = LLMTracklistParser(model="gpt-4")
        result = parser.parse("<html>Test content</html>")

        assert result == mock_tracklist
        mock_client.responses.parse.assert_called_once_with(
            model="gpt-4",  # Should use custom model
            text_format=DomainTracklist,
            input=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that parses tracklists from HTML content.",
                },
                {"role": "user", "content": "<html>Test content</html>"},
            ],
        )

    @patch("whats_this_id.core.parsers.llm_parser.OpenAI")
    def test_parse_empty_content(self, mock_openai):
        """Test parsing with empty content."""
        # Setup mock client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_tracklist = Mock(spec=DomainTracklist)
        mock_tracklist.tracks = []

        mock_response = Mock()
        mock_response.output_parsed = mock_tracklist
        mock_client.responses.parse.return_value = mock_response

        parser = LLMTracklistParser()
        result = parser.parse("")

        assert result == mock_tracklist
        mock_client.responses.parse.assert_called_once_with(
            model="gpt-4o-mini",
            text_format=DomainTracklist,
            input=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that parses tracklists from HTML content.",
                },
                {"role": "user", "content": ""},
            ],
        )

    @patch("whats_this_id.core.parsers.llm_parser.OpenAI")
    def test_parse_exception(self, mock_openai):
        """Test parsing when OpenAI API raises an exception."""
        # Setup mock client to raise exception
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.responses.parse.side_effect = Exception("API Error")

        parser = LLMTracklistParser()

        with pytest.raises(Exception, match="API Error"):
            parser.parse("<html>Test content</html>")

    @patch("whats_this_id.core.parsers.llm_parser.OpenAI")
    def test_parse_with_complex_html(self, mock_openai):
        """Test parsing with complex HTML content."""
        # Setup mock client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_tracklist = Mock(spec=DomainTracklist)
        mock_tracklist.tracks = []

        mock_response = Mock()
        mock_response.output_parsed = mock_tracklist
        mock_client.responses.parse.return_value = mock_response

        complex_html = """
        <html>
            <body>
                <div class="tracklist">
                    <h1>DJ Set Tracklist</h1>
                    <ul>
                        <li>Track 1 - Artist 1</li>
                        <li>Track 2 - Artist 2</li>
                    </ul>
                </div>
            </body>
        </html>
        """

        parser = LLMTracklistParser()
        result = parser.parse(complex_html)

        assert result == mock_tracklist
        mock_client.responses.parse.assert_called_once_with(
            model="gpt-4o-mini",
            text_format=DomainTracklist,
            input=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that parses tracklists from HTML content.",
                },
                {"role": "user", "content": complex_html},
            ],
        )

    @patch("whats_this_id.core.parsers.llm_parser.OpenAI")
    def test_parse_returns_domain_tracklist(self, mock_openai):
        """Test that parse returns a DomainTracklist object."""
        # Setup mock client and response
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_tracklist = Mock(spec=DomainTracklist)
        mock_tracklist.tracks = []

        mock_response = Mock()
        mock_response.output_parsed = mock_tracklist
        mock_client.responses.parse.return_value = mock_response

        parser = LLMTracklistParser()
        result = parser.parse("<html>Test</html>")

        assert isinstance(result, DomainTracklist)
        assert result == mock_tracklist
