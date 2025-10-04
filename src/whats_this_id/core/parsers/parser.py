"""
Unified parser that handles all content parsing operations.
"""

import re
from typing import Any, List, Tuple

from bs4 import BeautifulSoup
from dj_set_downloader.models.domain_tracklist import DomainTrack

from whats_this_id.core.common import BaseOperation, ExecutionResult


class Parser(BaseOperation):
    """Unified parser that handles tracklist parsing using HTML parsing."""

    def __init__(
        self, model: str = "gpt-4o-mini", timeout: int = 15, max_retries: int = 3
    ):
        super().__init__("Parser", timeout, max_retries)
        self.model = model  # Keep for future LLM implementation

    def supports(self, content_type: str) -> bool:
        """Check if this parser supports the given content type."""
        return content_type == "html"

    async def _execute_async(self, content: str) -> Tuple[List[Any], float]:
        """Parse tracklist from HTML content using HTML parsing."""
        print(
            f"🔍 Parser: Starting HTML parsing with {len(content)} characters of content..."
        )

        try:
            # Parse HTML content
            soup = BeautifulSoup(content, "html.parser")

            # Look for common tracklist patterns
            tracks = self._extract_tracks_from_html(soup)

            confidence = self._calculate_confidence(tracks, content)

            print(
                f"✅ Parser: Extracted {len(tracks)} tracks with confidence {confidence:.2f}"
            )
            return tracks, confidence

        except Exception as e:
            print(f"❌ Parser: HTML parsing failed: {e}")
            raise

    def _extract_tracks_from_html(self, soup: BeautifulSoup) -> List[Any]:
        """Extract tracks from parsed HTML."""
        tracks = []

        # 1001tracklists.com specific patterns
        # Pattern 1: Look for tlpItem elements (main tracklist items)
        tlp_elements = soup.find_all("div", class_=re.compile(r"tlpItem", re.I))
        print(f"🔍 Found {len(tlp_elements)} tlpItem elements")

        for element in tlp_elements:
            track_info = self._extract_track_info_from_tlp_element(element, soup)
            if track_info:
                tracks.append(track_info)

        # Sort tracks by track number
        tracks.sort(key=lambda x: x.track_number if x.track_number is not None else 999)

        # Pattern 2: Look for other track-related elements
        if not tracks:
            track_elements = soup.find_all(
                ["div", "li", "tr"], class_=re.compile(r"track|song|item", re.I)
            )
            print(f"🔍 Found {len(track_elements)} other track elements")

            for element in track_elements:
                track_info = self._extract_track_info(element)
                if track_info:
                    tracks.append(track_info)

        # Pattern 3: Look for elements with tlp_ class (specific track IDs)
        if not tracks:
            tlp_id_elements = soup.find_all("div", class_=re.compile(r"tlp_\d+", re.I))
            print(f"🔍 Found {len(tlp_id_elements)} tlp_ elements")

            for element in tlp_id_elements:
                track_info = self._extract_track_info_from_tlp_element(element)
                if track_info:
                    tracks.append(track_info)

        # Pattern 4: Look for any text that looks like "Artist - Track"
        if not tracks:
            all_text = soup.get_text()
            lines = all_text.split("\n")
            for line in lines:
                line = line.strip()
                if " - " in line and len(line) > 10 and len(line) < 200:
                    track_info = self._extract_track_info_from_text(line)
                    if track_info:
                        tracks.append(track_info)

        return tracks

    def _extract_track_info(self, element) -> Any:
        """Extract track information from a single element."""
        text = element.get_text(strip=True)

        # Skip empty or very short text
        if len(text) < 5:
            return None

        # Look for patterns like "Artist - Track" or "Track by Artist"
        # This is a simple implementation - can be enhanced later
        if " - " in text or " by " in text:
            if " - " in text:
                parts = text.split(" - ", 1)
                artist = parts[0].strip()
                track = parts[1].strip()
            else:
                parts = text.split(" by ", 1)
                track = parts[0].strip()
                artist = parts[1].strip() if len(parts) > 1 else ""

            return DomainTrack(
                name=track,
                artist=artist,
                available=False,
                download_url=None,
                end_time=None,
                size_bytes=None,
                start_time=None,
                track_number=None,
            )

        return None

    def _extract_track_info_from_tlp_element(self, element, soup) -> Any:
        """Extract track information from a tlpItem element."""
        text = element.get_text()

        # Skip empty or very short text
        if len(text) < 5:
            return None

        # Extract track number and start time
        track_number, start_time = self._extract_track_number_and_time(text)

        # Check if this is an ID track (unreleased track)
        is_id_track = (
            element.get("data-isid") == "true"
            or "id - id" in text.lower()
            or " - id" in text.lower()
        )

        if is_id_track:
            # This is an ID track - look for suggestions
            suggestion = self._find_suggestion_for_id_track(element, soup)
            if suggestion:
                # Use the suggestion
                artist, track = suggestion
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
            else:
                # No suggestion found, use "ID - ID"
                return DomainTrack(
                    name="ID",
                    artist="ID",
                    available=False,
                    download_url=None,
                    end_time=None,
                    size_bytes=None,
                    start_time=start_time,
                    track_number=track_number,
                )

        # Regular track parsing
        # The format is typically: "01 02:30 Artist - Track Label info"
        if " - " in text:
            parts = text.split(" - ")
            if len(parts) >= 2:
                # The track is everything after the first ' - '
                track_part = parts[1].strip()

                # Clean up the track (remove label, extra info)
                # Be more careful about what we remove - don't remove single letters like "I"
                track = re.sub(
                    r"\s+[A-Z\s]{4,}\s+\d+.*$", "", track_part
                )  # Remove label and numbers at end (only if label is 4+ chars)
                track = re.sub(r"\s*\[.*?\]\s*$", "", track)  # Remove [label] info
                track = re.sub(r"\s*\(.*?\)\s*$", "", track)  # Remove (info)
                # Remove extra text that appears after the track name (like "OFUNSOUNDMIND  [edit?]     11    ewwcolton (19k)                 Save 10")
                track = re.sub(
                    r"\s+[A-Z]+\s+\[.*?\].*$", "", track
                )  # Remove text like "OFUNSOUNDMIND  [edit?] ..."
                track = re.sub(
                    r"\s+\d+\s+[a-zA-Z0-9()\s]+\s+Save.*$", "", track
                )  # Remove text like "11    ewwcolton (19k)                 Save 10"
                track = track.strip()

                # The artist is in the part before the first ' - '
                artist_part = parts[0].strip()

                # Remove track number and timestamp from the beginning
                # Pattern: "01 02:30 Artist" or "01 Artist" or "25 2:01:30 Artist"
                artist = re.sub(
                    r"^\d+\s+\d+:\d+(?::\d+)?\s+", "", artist_part
                )  # Remove "01 02:30 " or "25 2:01:30 "
                artist = re.sub(r"^\d+\s+", "", artist)  # Remove "01 "
                artist = artist.strip()

                # Skip if too short
                if len(artist) > 1 and len(track) > 1:
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

        return None

    def _extract_track_number_and_time(self, text: str) -> tuple:
        """Extract track number and start time from text."""
        track_number = None
        start_time = None

        # Look for track number pattern: "01", "02", etc.
        # Pattern: "01        ID - ID" or "02   02:30      Artist - Track"
        track_match = re.search(r"^\s*(\d+)\s+", text)
        if track_match:
            track_number = int(track_match.group(1))

        # Look for time pattern: "02:30", "08:12", "2:01:30", etc.
        # Pattern: "02   02:30      Artist - Track"
        time_match = re.search(r"^\s*\d+\s+(\d+:\d+(?::\d+)?)\s+", text)
        if time_match:
            start_time = time_match.group(1)

        return track_number, start_time

    def _find_suggestion_for_id_track(self, element, soup) -> tuple:
        """Find suggestion for an ID track."""
        # Get the track ID from the element
        track_id = element.get("data-id")
        if not track_id:
            return None

        # Look for suggestion container with class tlp_<track_id> in the full HTML
        suggestion_container = soup.find("div", class_=re.compile(f"tlp_{track_id}"))

        if suggestion_container:
            # Find the suggestion within this container
            suggestion = suggestion_container.find(
                "div", id=re.compile(r"sug\d+_value")
            )
            if suggestion:
                suggestion_text = suggestion.get_text().strip()
                if " - " in suggestion_text:
                    parts = suggestion_text.split(" - ", 1)
                    artist = parts[0].strip()
                    track = parts[1].strip()

                    # Clean up the track (remove label info)
                    track = re.sub(r"\s*\[.*?\]\s*$", "", track)  # Remove [label] info
                    track = track.strip()

                    return artist, track

        # Look for suggestion elements in siblings
        siblings = element.find_next_siblings()
        for sibling in siblings:
            suggestions = sibling.find_all("div", id=re.compile(r"sug\d+_value"))
            if suggestions:
                suggestion_text = suggestions[0].get_text().strip()
                if " - " in suggestion_text:
                    parts = suggestion_text.split(" - ", 1)
                    artist = parts[0].strip()
                    track = parts[1].strip()

                    # Clean up the track (remove label info)
                    track = re.sub(r"\s*\[.*?\]\s*$", "", track)  # Remove [label] info
                    track = track.strip()

                    return artist, track

        return None

    def _extract_track_info_from_text(self, text: str) -> Any:
        """Extract track information from text."""
        # Skip empty or very short text
        if len(text) < 5:
            return None

        # Look for patterns like "Artist - Track" or "Track by Artist"
        if " - " in text or " by " in text:
            # Filter out obvious non-track text
            if any(
                skip_word in text.lower()
                for skip_word in [
                    "copyright",
                    "rights",
                    "reserved",
                    "tracklist",
                    "playlist",
                ]
            ):
                return None

            if " - " in text:
                parts = text.split(" - ", 1)
                artist = parts[0].strip()
                track = parts[1].strip()
            else:
                parts = text.split(" by ", 1)
                track = parts[0].strip()
                artist = parts[1].strip() if len(parts) > 1 else ""

            return DomainTrack(
                name=track,
                artist=artist,
                available=False,
                download_url=None,
                end_time=None,
                size_bytes=None,
                start_time=None,
                track_number=None,
            )

        return None

    def _calculate_confidence(self, tracks: List[Any], content: str) -> float:
        """Calculate confidence based on track count and content quality."""
        if not tracks:
            return 0.0

        # Base confidence on track count
        track_count = len(tracks)
        if track_count >= 10:
            base_confidence = 0.9
        elif track_count >= 5:
            base_confidence = 0.7
        elif track_count >= 2:
            base_confidence = 0.5
        else:
            base_confidence = 0.3

        # Adjust based on content length (more content = higher confidence)
        content_length = len(content)
        if content_length > 5000:
            length_factor = 1.0
        elif content_length > 2000:
            length_factor = 0.9
        elif content_length > 1000:
            length_factor = 0.8
        else:
            length_factor = 0.6

        return min(1.0, base_confidence * length_factor)

    def parse(self, content: str) -> Tuple[List[Any], float]:
        """Synchronous parse method for backward compatibility."""
        result = self.execute(content)
        if result.success:
            return result.data
        return [], 0.0
