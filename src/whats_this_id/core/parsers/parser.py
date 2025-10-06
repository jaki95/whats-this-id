"""
Parser that handles all content parsing operations.
"""

import asyncio
import datetime
import re
from typing import Any

from bs4 import BeautifulSoup

from whats_this_id.core.common import BaseOperation, DomainTrack, logger

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
    "timestamp_prefix": re.compile(r"^\d+:\d+(?::\d+)?\s*"),
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

    def parse(self, content: str) -> tuple[list[DomainTrack], float, str | None, dict]:
        """Parse content synchronously and return tracks with confidence score, total duration, and metadata.

        Args:
            content: HTML content to parse

        Returns:
            Tuple of (tracks, confidence_score, total_duration, metadata)
        """
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            tracks, total_duration, metadata = loop.run_until_complete(
                self._execute_async(content)
            )
        finally:
            loop.close()

        # Calculate confidence based on number of tracks found
        confidence = min(1.0, len(tracks) / 10.0) if tracks else 0.0

        return tracks, confidence, total_duration, metadata

    async def _execute_async(
        self, content: str
    ) -> tuple[list[DomainTrack], str | None, dict]:
        """Parse tracklist from HTML content using HTML parsing."""
        logger.info(f"Parser: Starting HTML parsing with {len(content)} characters...")

        try:
            soup = BeautifulSoup(content, "html.parser")
            total_duration = self._extract_total_duration(soup)
            logger.info(f"Parser: Extracted total_duration: {total_duration}")

            # Extract DJ set metadata
            metadata = self._extract_dj_set_metadata(soup)
            logger.info(f"Parser: Extracted metadata: {metadata}")

            tracks = self._extract_tracks_from_html(soup, total_duration)

            logger.info(f"Parser: Extracted {len(tracks)} tracks.")
            return tracks, total_duration, metadata

        except Exception as e:
            logger.error(f"Parser: HTML parsing failed: {e}")
            raise

    def _extract_tracks_from_html(
        self, soup: BeautifulSoup, total_duration: str | None = None
    ) -> list[Any]:
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
                    # Filter out None values
                    valid_tracks = [
                        track for track in pattern_tracks if track is not None
                    ]
                    if valid_tracks:
                        tracks.extend(valid_tracks)
                        logger.info(
                            f"Found {len(valid_tracks)} tracks using {pattern_name}"
                        )

        # Sort tracks by track number
        tracks.sort(key=lambda x: x.track_number if x.track_number is not None else 999)

        # Apply timing rules with total duration
        tracks = self._apply_timing_rules(tracks, total_duration)

        return tracks

    def _extract_total_duration(self, soup: BeautifulSoup) -> str | None:
        """Extract the total duration of the DJ set from the 1001tracklists page."""
        # Get all text content for comprehensive search
        all_text = soup.get_text()

        # Debug: Log a sample of the HTML content to understand the structure
        logger.debug(f"HTML content sample: {all_text[:500]}...")

        # More comprehensive patterns for 1001tracklists
        # Order matters - more specific patterns first
        text_patterns = [
            # Player duration patterns
            r"Player\s+\d+\s*\[(\d+:\d+(?::\d+)?)\]",
            # Standard duration patterns
            r"Duration:?\s*(\d+:\d+(?::\d+)?)",
            r"Length:?\s*(\d+:\d+(?::\d+)?)",
            r"Time:?\s*(\d+:\d+(?::\d+)?)",
            r"Total:?\s*(\d+:\d+(?::\d+)?)",
            # 1001tracklists specific patterns
            r"(\d+:\d+(?::\d+)?)\s*set",
            r"(\d+:\d+(?::\d+)?)\s*mix",
            r"(\d+:\d+(?::\d+)?)\s*show",
            r"(\d+:\d+(?::\d+)?)\s*episode",
            # Look for time patterns in various contexts
            r"(\d+:\d+(?::\d+)?)\s*(?:total|complete|full)",
            r"(?:total|complete|full)\s*(\d+:\d+(?::\d+)?)",
            # Look for time patterns that might be durations (longer than typical track times)
            r"(\d+:\d{2}:\d{2})",  # hh:mm:ss format
            # Lower priority patterns (these might match track times)
            r"(\d+:\d+(?::\d+)?)\s*(?:min|hour|hr|h|m)",
            r"(\d+:\d+(?::\d+)?)\s*duration",
            r"(\d+:\d+(?::\d+)?)\s*length",
            r"(\d{2}:\d{2})",  # mm:ss format (but be careful not to match track times)
        ]

        # Check text-based patterns
        for pattern in text_patterns:
            matches = re.findall(pattern, all_text, re.I)
            for match in matches:
                duration = match
                # Validate that this looks like a reasonable duration
                if self._is_valid_duration(duration):
                    logger.info(f"Found total duration in text: {duration}")
                    return duration

        # Also check specific HTML elements that might contain duration
        element_patterns = [
            soup.find("span", class_=re.compile(r"duration|length|time", re.I)),
            soup.find(
                "div", class_=re.compile(r"tracklist.*info|info.*tracklist", re.I)
            ),
            soup.find("div", class_=re.compile(r"header|info|meta", re.I)),
            soup.find("h1", string=re.compile(r"\d+:\d+")),
            soup.find("h2", string=re.compile(r"\d+:\d+")),
            soup.find("h3", string=re.compile(r"\d+:\d+")),
            soup.find("p", string=re.compile(r"\d+:\d+")),
            soup.find("div", string=re.compile(r"\d+:\d+")),
        ]

        for element in element_patterns:
            if element:
                if hasattr(element, "get_text"):
                    text = element.get_text()
                else:
                    text = str(element)

                # Look for time pattern in the element text
                time_match = re.search(r"(\d+:\d+(?::\d+)?)", text)
                if time_match:
                    duration = time_match.group(1)
                    if self._is_valid_duration(duration):
                        logger.info(f"Found total duration in element: {duration}")
                        return duration

        # If no duration found, return None
        logger.warning("Could not extract total duration from page")
        return None

    def _is_valid_duration(self, duration: str) -> bool:
        """Check if a duration string looks like a valid total duration."""
        try:
            parts = duration.split(":")
            if len(parts) == 2:  # mm:ss
                minutes, seconds = int(parts[0]), int(parts[1])
                total_minutes = minutes + seconds / 60
                # Reasonable duration range: 30 minutes to 8 hours
                return 30 <= total_minutes <= 480
            elif len(parts) == 3:  # hh:mm:ss
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                total_minutes = hours * 60 + minutes + seconds / 60
                # Reasonable duration range: 30 minutes to 8 hours
                return 30 <= total_minutes <= 480
            else:
                return False
        except (ValueError, AttributeError):
            return False

    def _calculate_duration_between_times(self, start_time: str, end_time: str) -> int:
        """Calculate duration in seconds between two time strings (hh:mm:ss or mm:ss)."""
        try:
            start_seconds = self._time_to_seconds(start_time)
            end_seconds = self._time_to_seconds(end_time)
            return end_seconds - start_seconds
        except (ValueError, AttributeError):
            return 0

    def _time_to_seconds(self, time_str: str) -> int:
        """Convert time string (hh:mm:ss or mm:ss) to seconds."""
        parts = time_str.split(":")
        if len(parts) == 2:  # mm:ss
            minutes, seconds = int(parts[0]), int(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:  # hh:mm:ss
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"Invalid time format: {time_str}")

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

        # Apply cleaning to the extracted text
        artist = self._clean_artist_name(artist)
        track = self._clean_track_name(track)

        return self._create_domain_track(track, artist)

    def _create_domain_track(
        self,
        track: str,
        artist: str,
        track_number: int | None = None,
        start_time: str | None = None,
    ) -> DomainTrack:
        """Create a DomainTrack object with common defaults."""
        # Apply cleaning to ensure consistency
        clean_artist = self._clean_artist_name(artist)
        clean_track = self._clean_track_name(track)

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

    def _extract_track_info_from_tlp_element(self, element, soup=None) -> Any:
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
        if self._is_id_track(element, element.get_text()):
            return self._handle_id_track(element, soup, track_number, start_time)

        # Extract artist and track name from structured elements
        return self._extract_structured_track_info(element, track_number, start_time)

    def _extract_structured_track_info(
        self, element, track_number: int | None, start_time: str | None
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
                    artist = self._clean_artist_name(parts[0].strip())
                    track = self._clean_track_name(parts[1].strip())

                    # Skip if the track name contains problematic patterns
                    if (
                        "[The Gods Planet]" in track
                        or len(track) > 100
                        or track.count("[") > 1
                        or track.count("(") > 1
                    ):
                        continue

                    if len(artist) > 1 and len(track) > 1:
                        return self._create_domain_track(
                            track, artist, track_number, start_time
                        )

        # If no clean format found, try to extract from the full text
        text = element.get_text()
        if " - " in text:
            parts = text.split(" - ", 1)
            if len(parts) == 2:
                artist = self._clean_artist_name(parts[0].strip())
                track = self._clean_track_name(parts[1].strip())

                if len(track) > 100 or track.count("[") > 1 or track.count("(") > 1:
                    return None

                if len(artist) > 1 and len(track) > 1:
                    return self._create_domain_track(
                        track, artist, track_number, start_time
                    )

        return None

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
            CLEANUP_PATTERNS["timestamp_prefix"],
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

        # Log for debugging
        if "[The Gods Planet]" in text or "37:00Woo York" in text:
            logger.info(
                f"Found problematic text in _extract_track_info_from_text: {text[:100]}"
            )

        return self._parse_artist_track_text(text)

    def _apply_timing_rules(
        self, tracks: list[DomainTrack], total_duration: str | None = None
    ) -> list[DomainTrack]:
        """Apply timing rules to tracks:
        1. First track should always start at 00:00
        2. End time of a track is the start time of the next track
        3. Last track end time is set to the total duration of the set
        """
        if not tracks:
            return tracks

        logger.info(
            f"Applying timing rules to {len(tracks)} tracks, total_duration: {total_duration}"
        )

        # Rule 1: First track always starts at 00:00
        if tracks[0].start_time != "00:00":
            tracks[0].start_time = "00:00"

        # Rule 2: Set end times based on next track's start time
        for i in range(len(tracks)):
            if i < len(tracks) - 1:
                # Set end time to the start time of the next track
                tracks[i].end_time = tracks[i + 1].start_time
            else:
                # Last track - set end time to the total duration of the set
                if total_duration:
                    tracks[i].end_time = total_duration
                    logger.info(
                        f"Set last track end time to total duration: {total_duration}"
                    )
                else:
                    # No total duration available - leave end_time as None
                    # This indicates that the duration extraction failed
                    tracks[i].end_time = None
                    logger.warning("No total duration available for last track")

        return tracks

    def _extract_dj_set_metadata(self, soup: BeautifulSoup) -> dict:
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
                        title_text = self._clean_title_text(title_text)

                        # Try to extract DJ set name and artist from title
                        dj_set_name, artist = self._parse_dj_set_title(title_text)
                        if dj_set_name and artist:
                            metadata["name"] = dj_set_name
                            metadata["artist"] = artist
                            break

            # If we didn't find a structured title, try to extract from the page content
            if not metadata["name"] or not metadata["artist"]:
                # Look for common patterns in the text
                dj_set_name, artist = self._extract_dj_set_from_text_patterns(all_text)
                if dj_set_name and artist:
                    metadata["name"] = dj_set_name
                    metadata["artist"] = artist

            # Extract year if available
            year = self._extract_year(all_text)
            if year:
                metadata["year"] = year

            # Extract genre if available
            genre = self._extract_genre(all_text)
            if genre:
                metadata["genre"] = genre

            logger.info(f"Extracted DJ set metadata: {metadata}")

        except Exception as e:
            logger.warning(f"Failed to extract DJ set metadata: {e}")

        return metadata

    def _clean_title_text(self, text: str) -> str:
        """Clean title text by removing common unwanted patterns."""
        # Remove common website suffixes
        text = re.sub(r"\s*-\s*1001tracklists\.com.*$", "", text, flags=re.I)
        text = re.sub(r"\s*-\s*tracklist.*$", "", text, flags=re.I)
        text = re.sub(r"\s*-\s*mix.*$", "", text, flags=re.I)
        text = re.sub(r"\s*-\s*set.*$", "", text, flags=re.I)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _parse_dj_set_title(self, title: str) -> tuple[str | None, str | None]:
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

    def _extract_dj_set_from_text_patterns(
        self, text: str
    ) -> tuple[str | None, str | None]:
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

    def _extract_year(self, text: str) -> int | None:
        """Extract year from text content.

        Args:
            text: The text content to search

        Returns:
            Year as integer or None if not found
        """
        # Look for 4-digit years between 1990 and current year + 1
        current_year = datetime.now().year
        year_pattern = r"\b(19[9]\d|20[0-2]\d)\b"

        matches = re.findall(year_pattern, text)
        for match in matches:
            year = int(match)
            if 1990 <= year <= current_year + 1:
                return year

        return None

    def _extract_genre(self, text: str) -> str | None:
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
