"""
Metadata extraction utilities for DJ sets.
"""

import datetime
import re

from bs4 import BeautifulSoup

from whats_this_id.core.common import logger
from whats_this_id.core.parsers.text_cleaners import TextCleaner


class MetadataExtractor:
    """Utility class for extracting DJ set metadata."""

    @staticmethod
    def extract_dj_set_metadata(soup: BeautifulSoup) -> dict:
        """Extract DJ set name and artist from the HTML content.

        Args:
            soup: BeautifulSoup object of the HTML content

        Returns:
            Dictionary containing extracted metadata (name, artist, year, genre)
        """
        metadata = {"name": None, "artist": None, "year": None, "genre": None}

        try:
            # Get all text content for comprehensive search
            all_text = soup.get_text()

            # Look for title patterns in various HTML elements
            title_elements = [
                soup.find("h1"),
                soup.find("h2"),
                soup.find("h3"),
                soup.find("title"),
                soup.find("div", class_=re.compile(r"title|header|name", re.I)),
                soup.find("span", class_=re.compile(r"title|header|name", re.I)),
            ]

            # Extract title from elements
            for element in title_elements:
                if element:
                    title_text = element.get_text().strip()
                    if title_text and len(title_text) > 3:
                        # Clean up the title text
                        title_text = TextCleaner.clean_title_text(title_text)

                        # Try to extract DJ set name and artist from title
                        dj_set_name, artist = MetadataExtractor._parse_dj_set_title(
                            title_text
                        )
                        if dj_set_name and artist:
                            metadata["name"] = dj_set_name
                            metadata["artist"] = artist
                            break

            # If we didn't find a structured title, try to extract from the page content
            if not metadata["name"] or not metadata["artist"]:
                # Look for common patterns in the text
                dj_set_name, artist = (
                    MetadataExtractor._extract_dj_set_from_text_patterns(all_text)
                )
                if dj_set_name and artist:
                    metadata["name"] = dj_set_name
                    metadata["artist"] = artist

            # Extract year if available
            year = MetadataExtractor._extract_year(all_text)
            if year:
                metadata["year"] = year

            # Extract genre if available
            genre = MetadataExtractor._extract_genre(all_text)
            if genre:
                metadata["genre"] = genre

            logger.info(f"Extracted DJ set metadata: {metadata}")

        except Exception as e:
            logger.warning(f"Failed to extract DJ set metadata: {e}")

        return metadata

    @staticmethod
    def _parse_dj_set_title(title: str) -> tuple[str | None, str | None]:
        """Parse DJ set name and artist from a title string.

        Args:
            title: The title string to parse

        Returns:
            Tuple of (dj_set_name, artist) or (None, None) if parsing fails
        """
        if not title or len(title) < 3:
            return None, None

        # Common patterns for DJ set titles
        patterns = [
            # "Artist - Set Name" format
            r"^([^-]+?)\s*-\s*(.+)$",
            # "Set Name by Artist" format
            r"^(.+?)\s+by\s+(.+)$",
            # "Artist: Set Name" format
            r"^([^:]+?):\s*(.+)$",
            # "Set Name (Artist)" format
            r"^(.+?)\s*\(([^)]+)\)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, title, re.I)
            if match:
                if pattern.startswith(r"^([^-]+?)\s*-\s*(.+)$"):
                    # "Artist - Set Name" format
                    artist, dj_set_name = match.groups()
                elif pattern.startswith(r"^(.+?)\s+by\s+(.+)$"):
                    # "Set Name by Artist" format
                    dj_set_name, artist = match.groups()
                elif pattern.startswith(r"^([^:]+?):\s*(.+)$"):
                    # "Artist: Set Name" format
                    artist, dj_set_name = match.groups()
                elif pattern.startswith(r"^(.+?)\s*\(([^)]+)\)$"):
                    # "Set Name (Artist)" format
                    dj_set_name, artist = match.groups()

                # Clean up the extracted values
                artist = artist.strip() if artist else None
                dj_set_name = dj_set_name.strip() if dj_set_name else None

                # Validate that we have meaningful content
                if (
                    artist
                    and len(artist) > 1
                    and dj_set_name
                    and len(dj_set_name) > 1
                    and len(artist) < 100
                    and len(dj_set_name) < 200
                ):
                    return dj_set_name, artist

        return None, None

    @staticmethod
    def _extract_dj_set_from_text_patterns(text: str) -> tuple[str | None, str | None]:
        """Extract DJ set name and artist from text using various patterns.

        Args:
            text: The text content to search

        Returns:
            Tuple of (dj_set_name, artist) or (None, None) if extraction fails
        """
        # Look for common DJ set patterns in the text
        patterns = [
            # "Artist - Set Name" pattern
            r"([A-Za-z0-9\s&]+?)\s*-\s*([A-Za-z0-9\s&]+?)(?:\s|$|\.|,|;|:)",
            # "Set Name by Artist" pattern
            r"([A-Za-z0-9\s&]+?)\s+by\s+([A-Za-z0-9\s&]+?)(?:\s|$|\.|,|;|:)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.I)
            for match in matches:
                if pattern.startswith(r"([A-Za-z0-9\s&]+?)\s*-\s*([A-Za-z0-9\s&]+?)"):
                    # "Artist - Set Name" format
                    artist, dj_set_name = match
                else:
                    # "Set Name by Artist" format
                    dj_set_name, artist = match

                # Clean up the extracted values
                artist = artist.strip() if artist else None
                dj_set_name = dj_set_name.strip() if dj_set_name else None

                # Validate that we have meaningful content
                if (
                    artist
                    and len(artist) > 2
                    and len(artist) < 50
                    and dj_set_name
                    and len(dj_set_name) > 2
                    and len(dj_set_name) < 100
                ):
                    return dj_set_name, artist

        return None, None

    @staticmethod
    def _extract_year(text: str) -> int | None:
        """Extract year from text content.

        Args:
            text: The text content to search

        Returns:
            Year as integer or None if not found
        """
        # Look for 4-digit years between 1990 and current year + 1
        current_year = datetime.datetime.now().year
        year_pattern = r"\b(19[9]\d|20[0-2]\d)\b"

        matches = re.findall(year_pattern, text)
        for match in matches:
            year = int(match)
            if 1990 <= year <= current_year + 1:
                return year

        return None

    @staticmethod
    def _extract_genre(text: str) -> str | None:
        """Extract genre from text content.

        Args:
            text: The text content to search

        Returns:
            Genre string or None if not found
        """
        # Common electronic music genres
        genres = [
            "techno",
            "house",
            "trance",
            "progressive",
            "deep house",
            "tech house",
            "minimal",
            "ambient",
            "dubstep",
            "drum and bass",
            "dnb",
            "breakbeat",
            "electro",
            "electronic",
            "edm",
            "progressive house",
            "melodic techno",
            "dark techno",
            "industrial",
            "experimental",
            "psytrance",
            "goa",
            "hardstyle",
            "hardcore",
            "garage",
            "bass",
            "future bass",
            "trap",
        ]

        text_lower = text.lower()
        for genre in genres:
            if genre in text_lower:
                return genre.title()

        return None
