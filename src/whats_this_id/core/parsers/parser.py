"""
Parser that handles all content parsing operations.
"""

import re
from typing import Any

from bs4 import BeautifulSoup
from dj_set_downloader.models.domain_track import DomainTrack

from whats_this_id.core.common import BaseOperation, logger

# Constants for track extraction patterns
TRACKLIST_PATTERNS = {
    "tlp_item": re.compile(r"tlpItem", re.I),
    "track_elements": re.compile(r"track|song|item", re.I),
    "tlp_id": re.compile(r"tlp_\d+", re.I),
    "suggestion_id": re.compile(r"sug\d+_value"),
}

# Text cleaning patterns
CLEANUP_PATTERNS = {
    "label_and_numbers": re.compile(r"\s+[A-Z\s]{4,}\s+\d+.*$"),
    "brackets": re.compile(r"\s*\[.*?\]\s*$"),
    "parentheses": re.compile(r"\s*\(.*?\)\s*$"),
    "edit_info": re.compile(r"\s+[A-Z]+\s+\[.*?\].*$"),
    "user_info": re.compile(r"\s+\d+\s+[a-zA-Z0-9()\s]+\s+Save.*$"),
    "track_number_time": re.compile(r"^\d+\s+\d+:\d+(?::\d+)?\s+"),
    "track_number": re.compile(r"^\d+\s+"),
}

# Skip words for text filtering
SKIP_WORDS = {"copyright", "rights", "reserved", "tracklist", "playlist"}


class Parser(BaseOperation):
    """Parser that handles tracklist parsing using HTML parsing."""

    def __init__(self, timeout: int = 15, max_retries: int = 3):
        super().__init__("Parser", timeout, max_retries)

    def supports(self, content_type: str) -> bool:
        """Check if this parser supports the given content type."""
        return content_type == "html"

    async def _execute_async(self, content: str) -> list[DomainTrack]:
        """Parse tracklist from HTML content using HTML parsing."""
        logger.info(f"Parser: Starting HTML parsing with {len(content)} characters...")

        try:
            soup = BeautifulSoup(content, "html.parser")
            tracks = self._extract_tracks_from_html(soup)

            logger.info(f"Parser: Extracted {len(tracks)} tracks.")
            return tracks

        except Exception as e:
            logger.error(f"Parser: HTML parsing failed: {e}")
            raise

    def _extract_tracks_from_html(self, soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from parsed HTML using multiple patterns."""
        tracks = []

        # Try different extraction patterns in order of specificity
        extraction_patterns = [
            ("tlpItem elements", lambda: self._extract_from_tlp_items(soup)),
            ("track elements", lambda: self._extract_from_track_elements(soup)),
            ("tlp ID elements", lambda: self._extract_from_tlp_ids(soup)),
            ("text patterns", lambda: self._extract_from_text_patterns(soup)),
        ]

        for pattern_name, extract_func in extraction_patterns:
            if not tracks:
                pattern_tracks = extract_func()
                if pattern_tracks:
                    tracks.extend(pattern_tracks)
                    logger.info(f"Found {len(pattern_tracks)} tracks using {pattern_name}")

        # Sort tracks by track number
        tracks.sort(key=lambda x: x.track_number if x.track_number is not None else 999)
        return tracks

    def _extract_from_tlp_items(self, soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from tlpItem elements."""
        elements = soup.find_all("div", class_=TRACKLIST_PATTERNS["tlp_item"])
        return [
            self._extract_track_info_from_tlp_element(el, soup) for el in elements if el
        ]

    def _extract_from_track_elements(self, soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from generic track elements."""
        elements = soup.find_all(
            ["div", "li", "tr"], class_=TRACKLIST_PATTERNS["track_elements"]
        )
        return [self._extract_track_info(el) for el in elements if el]

    def _extract_from_tlp_ids(self, soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from tlp ID elements."""
        elements = soup.find_all("div", class_=TRACKLIST_PATTERNS["tlp_id"])
        return [self._extract_track_info_from_tlp_element(el) for el in elements if el]

    def _extract_from_text_patterns(self, soup: BeautifulSoup) -> list[Any]:
        """Extract tracks from text patterns."""
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.split("\n")]
        return [
            self._extract_track_info_from_text(line)
            for line in lines
            if " - " in line and 10 < len(line) < 200
        ]

    def _extract_track_info(self, element) -> Any:
        """Extract track information from a single element."""
        text = element.get_text(strip=True)
        if len(text) < 5:
            return None

        return self._parse_artist_track_text(text)

    def _parse_artist_track_text(self, text: str) -> DomainTrack | None:
        """Parse artist and track from text with ' - ' or ' by ' separators."""
        if " - " in text:
            parts = text.split(" - ", 1)
            artist, track = parts[0].strip(), parts[1].strip()
        elif " by " in text:
            parts = text.split(" by ", 1)
            track, artist = parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
        else:
            return None

        return self._create_domain_track(track, artist)

    def _create_domain_track(
        self,
        track: str,
        artist: str,
        track_number: int | None = None,
        start_time: str | None = None,
    ) -> DomainTrack:
        """Create a DomainTrack object with common defaults."""
        return DomainTrack(
            name=track,
            artist=artist,
            available=False,
            download_url=None,
            end_time=None,
            size_bytes=None,
            start_time=start_time,
            track_number=track_number,
        )

    def _extract_track_info_from_tlp_element(self, element, soup=None) -> Any:
        """Extract track information from a tlpItem element."""
        text = element.get_text()
        if len(text) < 5:
            return None

        track_number, start_time = self._extract_track_number_and_time(text)

        if self._is_id_track(element, text):
            return self._handle_id_track(element, soup, track_number, start_time)

        return self._parse_regular_track(text, track_number, start_time)

    def _is_id_track(self, element, text: str) -> bool:
        """Check if this is an ID track (unreleased track)."""
        return (
            element.get("data-isid") == "true"
            or "id - id" in text.lower()
            or " - id" in text.lower()
        )

    def _handle_id_track(
        self, element, soup, track_number: int | None, start_time: str | None
    ) -> DomainTrack:
        """Handle ID track extraction with suggestions."""
        suggestion = self._find_suggestion_for_id_track(element, soup) if soup else None
        if suggestion:
            artist, track = suggestion
            return self._create_domain_track(track, artist, track_number, start_time)
        else:
            return self._create_domain_track("ID", "ID", track_number, start_time)

    def _parse_regular_track(
        self, text: str, track_number: int | None, start_time: str | None
    ) -> DomainTrack | None:
        """Parse regular track from text."""
        if " - " not in text:
            return None

        parts = text.split(" - ", 1)
        if len(parts) < 2:
            return None

        track = self._clean_track_name(parts[1].strip())
        artist = self._clean_artist_name(parts[0].strip())

        if len(artist) > 1 and len(track) > 1:
            return self._create_domain_track(track, artist, track_number, start_time)
        return None

    def _clean_track_name(self, track_part: str) -> str:
        """Clean track name by removing labels and extra info."""
        track = track_part
        for pattern in [
            CLEANUP_PATTERNS["label_and_numbers"],
            CLEANUP_PATTERNS["brackets"],
            CLEANUP_PATTERNS["parentheses"],
            CLEANUP_PATTERNS["edit_info"],
            CLEANUP_PATTERNS["user_info"],
        ]:
            track = pattern.sub("", track)
        return track.strip()

    def _clean_artist_name(self, artist_part: str) -> str:
        """Clean artist name by removing track numbers and timestamps."""
        artist = artist_part
        for pattern in [
            CLEANUP_PATTERNS["track_number_time"],
            CLEANUP_PATTERNS["track_number"],
        ]:
            artist = pattern.sub("", artist)
        return artist.strip()

    def _extract_track_number_and_time(
        self, text: str
    ) -> tuple[int | None, str | None]:
        """Extract track number and start time from text."""
        track_number = None
        start_time = None

        # Extract track number: "01", "02", etc.
        track_match = re.search(r"^\s*(\d+)\s+", text)
        if track_match:
            track_number = int(track_match.group(1))

        # Extract time: "02:30", "08:12", "2:01:30", etc.
        time_match = re.search(r"^\s*\d+\s+(\d+:\d+(?::\d+)?)\s+", text)
        if time_match:
            start_time = time_match.group(1)

        return track_number, start_time

    def _find_suggestion_for_id_track(self, element, soup) -> tuple[str, str] | None:
        """Find suggestion for an ID track."""
        track_id = element.get("data-id")
        if not track_id:
            return None

        # Look in suggestion container
        suggestion_container = soup.find("div", class_=re.compile(f"tlp_{track_id}"))
        if suggestion_container:
            suggestion = self._extract_suggestion_from_element(suggestion_container)
            if suggestion:
                return suggestion

        # Look in sibling elements
        for sibling in element.find_next_siblings():
            suggestions = sibling.find_all(
                "div", id=TRACKLIST_PATTERNS["suggestion_id"]
            )
            if suggestions:
                suggestion = self._extract_suggestion_from_element(suggestions[0])
                if suggestion:
                    return suggestion

        return None

    def _extract_suggestion_from_element(self, element) -> tuple[str, str] | None:
        """Extract artist and track from suggestion element."""
        suggestion_text = element.get_text().strip()
        if " - " not in suggestion_text:
            return None

        parts = suggestion_text.split(" - ", 1)
        artist = parts[0].strip()
        track = CLEANUP_PATTERNS["brackets"].sub("", parts[1].strip()).strip()
        return artist, track

    def _extract_track_info_from_text(self, text: str) -> Any:
        """Extract track information from text."""
        if len(text) < 5:
            return None

        # Filter out obvious non-track text
        if any(skip_word in text.lower() for skip_word in SKIP_WORDS):
            return None

        return self._parse_artist_track_text(text)
