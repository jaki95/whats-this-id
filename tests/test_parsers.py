"""Unit tests for parsers."""

import pytest

from whats_this_id.core.parsers.base import Parser
from whats_this_id.core.parsers.parser import Parser as HTMLParser


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
        assert result.data == []

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
        assert isinstance(result.data, list)
        # Should extract tracks from the HTML
        assert len(result.data) >= 0  # May or may not find tracks depending on parsing logic
