"""
Track extraction utilities for parsing different HTML structures.
"""

import re
from typing import Any

from bs4 import BeautifulSoup

from whats_this_id.core.common import DomainTrack, logger
from whats_this_id.core.parsers.text_cleaners import TextCleaner

# Constants for track extraction patterns
TRACKLIST_PATTERNS = {
    "tlp_item": re.compile(r"tlpItem", re.I),
    "track_elements": re.compile(r"track|song|item", re.I),
    "tlp_id": re.compile(r"tlp_\d+", re.I),
    "suggestion_id": re.compile(r"sug\d+_value"),
}


class TrackExtractors:
    """Utility class for extracting tracks from different HTML structures."""

    @staticmethod
    def extract_from_tlp_items(soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from tlpItem elements."""
        elements = soup.find_all("div", class_=TRACKLIST_PATTERNS["tlp_item"])
        return [
            TrackExtractors._extract_track_info_from_tlp_element(el, soup) for el in elements if el
        ]

    @staticmethod
    def extract_from_track_elements(soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from generic track elements."""
        elements = soup.find_all(
            ["div", "li", "tr"], class_=TRACKLIST_PATTERNS["track_elements"]
        )
        return [TrackExtractors._extract_track_info(el) for el in elements if el]

    @staticmethod
    def extract_from_tlp_ids(soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from tlp ID elements."""
        elements = soup.find_all("div", class_=TRACKLIST_PATTERNS["tlp_id"])
        return [TrackExtractors._extract_track_info_from_tlp_element(el) for el in elements if el]

    @staticmethod
    def extract_from_text_patterns(soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from text patterns."""
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.split("\n")]
        return [
            TrackExtractors._extract_track_info_from_text(line)
            for line in lines
            if " - " in line and 10 < len(line) < 200
        ]

    @staticmethod
    def _extract_track_info(element) -> Any:
        """Extract track information from a single element."""
        text = element.get_text(strip=True)
        if len(text) < 5:
            return None

        return TrackExtractors._parse_artist_track_text(text)

    @staticmethod
    def _parse_artist_track_text(text: str) -> DomainTrack | None:
        """Parse artist and track from text with ' - ' or ' by ' separators."""
        if " - " in text:
            parts = text.split(" - ", 1)
            artist, track = parts[0].strip(), parts[1].strip()
        elif " by " in text:
            parts = text.split(" by ", 1)
            track, artist = parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
        else:
            return None

        # Apply cleaning to the extracted text
        artist = TextCleaner.clean_artist_name(artist)
        track = TextCleaner.clean_track_name(track)

        return TrackExtractors._create_domain_track(track, artist)

    @staticmethod
    def _create_domain_track(
        track: str,
        artist: str,
        track_number: int | None = None,
        start_time: str | None = None,
    ) -> DomainTrack:
        """Create a DomainTrack object with common defaults."""
        # Apply cleaning to ensure consistency
        clean_artist = TextCleaner.clean_artist_name(artist)
        clean_track = TextCleaner.clean_track_name(track)

        return DomainTrack(
            name=clean_track,
            artist=clean_artist,
            available=False,
            download_url=None,
            end_time=None,
            size_bytes=None,
            start_time=start_time,
            track_number=track_number,
        )

    @staticmethod
    def _extract_track_info_from_tlp_element(element, soup=None) -> Any:
        """Extract track information from a tlpItem element."""
        # Extract track number from the structured element
        track_number_elem = element.find(
            "span", id=lambda x: x and "tracknumber_value" in x
        )
        track_number = None
        if track_number_elem:
            try:
                track_number = int(track_number_elem.get_text().strip())
            except (ValueError, AttributeError):
                pass

        # Extract start time from the structured element
        start_time_elem = element.find(
            "div", class_=lambda x: x and "cue" in str(x).lower()
        )
        start_time = None
        if start_time_elem:
            time_text = start_time_elem.get_text().strip()
            time_match = re.search(r"(\d+:\d+(?::\d+)?)", time_text)
            if time_match:
                start_time = time_match.group(1)

        # Check if this is an ID track
        if TrackExtractors._is_id_track(element, element.get_text()):
            return TrackExtractors._handle_id_track(element, soup, track_number, start_time)

        # Extract artist and track name from structured elements
        return TrackExtractors._extract_structured_track_info(element, track_number, start_time)

    @staticmethod
    def _extract_structured_track_info(
        element, track_number: int | None, start_time: str | None
    ) -> DomainTrack | None:
        """Extract artist and track name from structured HTML elements."""
        # Look for the main track content area that contains artist and track info
        # Based on the HTML analysis, we need to find the right spans

        # First, try to find spans that contain clean artist-track pairs
        spans = element.find_all("span")

        for span in spans:
            text = span.get_text().strip()
            if " - " in text and len(text) > 5 and len(text) < 200:
                # This looks like a clean artist - track format
                parts = text.split(" - ", 1)
                if len(parts) == 2:
                    artist = TextCleaner.clean_artist_name(parts[0].strip())
                    track = TextCleaner.clean_track_name(parts[1].strip())

                    # Skip if the track name contains problematic patterns
                    if (
                        "[The Gods Planet]" in track
                        or len(track) > 100
                        or track.count("[") > 1
                        or track.count("(") > 1
                    ):
                        continue

                    if len(artist) > 1 and len(track) > 1:
                        return TrackExtractors._create_domain_track(
                            track, artist, track_number, start_time
                        )

        # If no clean format found, try to extract from the full text
        text = element.get_text()
        if " - " in text:
            parts = text.split(" - ", 1)
            if len(parts) == 2:
                artist = TextCleaner.clean_artist_name(parts[0].strip())
                track = TextCleaner.clean_track_name(parts[1].strip())

                if len(track) > 100 or track.count("[") > 1 or track.count("(") > 1:
                    return None

                if len(artist) > 1 and len(track) > 1:
                    return TrackExtractors._create_domain_track(
                        track, artist, track_number, start_time
                    )

        return None

    @staticmethod
    def _is_id_track(element, text: str) -> bool:
        """Check if this is an ID track (unreleased track)."""
        return (
            element.get("data-isid") == "true"
            or "id - id" in text.lower()
            or " - id" in text.lower()
        )

    @staticmethod
    def _handle_id_track(
        element, soup, track_number: int | None, start_time: str | None
    ) -> DomainTrack:
        """Handle ID track extraction with suggestions."""
        suggestion = TrackExtractors._find_suggestion_for_id_track(element, soup) if soup else None
        if suggestion:
            artist, track = suggestion
            return TrackExtractors._create_domain_track(track, artist, track_number, start_time)
        else:
            return TrackExtractors._create_domain_track("ID", "ID", track_number, start_time)

    @staticmethod
    def _parse_regular_track(
        text: str, track_number: int | None, start_time: str | None
    ) -> DomainTrack | None:
        """Parse regular track from text."""
        if " - " not in text:
            return None

        parts = text.split(" - ", 1)
        if len(parts) < 2:
            return None

        track = TextCleaner.clean_track_name(parts[1].strip())
        artist = TextCleaner.clean_artist_name(parts[0].strip())

        if len(artist) > 1 and len(track) > 1:
            return TrackExtractors._create_domain_track(track, artist, track_number, start_time)
        return None

    @staticmethod
    def _find_suggestion_for_id_track(element, soup) -> tuple[str, str] | None:
        """Find suggestion for an ID track."""
        track_id = element.get("data-id")
        if not track_id:
            return None

        # Look in suggestion container
        suggestion_container = soup.find("div", class_=re.compile(f"tlp_{track_id}"))
        if suggestion_container:
            suggestion = TrackExtractors._extract_suggestion_from_element(suggestion_container)
            if suggestion:
                return suggestion

        # Look in sibling elements
        for sibling in element.find_next_siblings():
            suggestions = sibling.find_all(
                "div", id=TRACKLIST_PATTERNS["suggestion_id"]
            )
            if suggestions:
                suggestion = TrackExtractors._extract_suggestion_from_element(suggestions[0])
                if suggestion:
                    return suggestion

        return None

    @staticmethod
    def _extract_suggestion_from_element(element) -> tuple[str, str] | None:
        """Extract artist and track from suggestion element."""
        suggestion_text = element.get_text().strip()
        if " - " not in suggestion_text:
            return None

        parts = suggestion_text.split(" - ", 1)
        artist = parts[0].strip()
        track = re.sub(r"\s*\[.*?\]\s*$", "", parts[1].strip()).strip()
        return artist, track

    @staticmethod
    def _extract_track_info_from_text(text: str) -> Any:
        """Extract track information from text."""
        if len(text) < 5:
            return None

        # Filter out obvious non-track text
        if TextCleaner.should_skip_text(text):
            return None

        # Log for debugging
        if "[The Gods Planet]" in text or "37:00Woo York" in text:
            logger.info(
                f"Found problematic text in _extract_track_info_from_text: {text[:100]}"
            )

        return TrackExtractors._parse_artist_track_text(text)
