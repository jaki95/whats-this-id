"""
Text cleaning utilities for track and artist names.
"""

import re

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


class TextCleaner:
    """Utility class for cleaning track and artist names."""

    @staticmethod
    def clean_track_name(track_part: str) -> str:
        """Clean track name by removing labels and extra info."""
        track = track_part

        for pattern in [
            CLEANUP_PATTERNS["label_and_numbers"],
            # Skip brackets pattern as it removes valid track names like [Remix], [Original Mix]
            # CLEANUP_PATTERNS["brackets"],
            # Skip parentheses pattern as it's too aggressive and removes valid track names
            # CLEANUP_PATTERNS["parentheses"],
            CLEANUP_PATTERNS["edit_info"],
            CLEANUP_PATTERNS["user_info"],
        ]:
            track = pattern.sub("", track)

        return track.strip()

    @staticmethod
    def clean_artist_name(artist_part: str) -> str:
        """Clean artist name by removing track numbers and timestamps."""
        artist = artist_part

        for pattern in [
            CLEANUP_PATTERNS["track_number_time"],
            CLEANUP_PATTERNS["track_number"],
            CLEANUP_PATTERNS["timestamp_prefix"],
        ]:
            artist = pattern.sub("", artist)

        return artist.strip()

    @staticmethod
    def clean_title_text(text: str) -> str:
        """Clean title text by removing common unwanted patterns."""
        # Remove common website suffixes
        text = re.sub(r"\s*-\s*1001tracklists\.com.*$", "", text, flags=re.I)
        text = re.sub(r"\s*-\s*tracklist.*$", "", text, flags=re.I)
        text = re.sub(r"\s*-\s*mix.*$", "", text, flags=re.I)
        text = re.sub(r"\s*-\s*set.*$", "", text, flags=re.I)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def should_skip_text(text: str) -> bool:
        """Check if text should be skipped based on skip words."""
        return any(skip_word in text.lower() for skip_word in SKIP_WORDS)
