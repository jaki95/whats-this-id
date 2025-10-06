"""
Timing utilities for parsing and calculating track durations.
"""

import datetime
import re
from typing import Any

from whats_this_id.core.common import DomainTrack, logger


class TimingUtils:
    """Utility class for handling timing operations."""

    @staticmethod
    def is_valid_duration(duration: str) -> bool:
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

    @staticmethod
    def calculate_duration_between_times(start_time: str, end_time: str) -> int:
        """Calculate duration in seconds between two time strings (hh:mm:ss or mm:ss)."""
        try:
            start_seconds = TimingUtils.time_to_seconds(start_time)
            end_seconds = TimingUtils.time_to_seconds(end_time)
            return end_seconds - start_seconds
        except (ValueError, AttributeError):
            return 0

    @staticmethod
    def time_to_seconds(time_str: str) -> int:
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

    @staticmethod
    def extract_track_number_and_time(text: str) -> tuple[int | None, str | None]:
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

    @staticmethod
    def apply_timing_rules(
        tracks: list[DomainTrack], total_duration: str | None = None
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

    @staticmethod
    def extract_total_duration_from_text(text: str) -> str | None:
        """Extract the total duration of the DJ set from text content."""
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
            matches = re.findall(pattern, text, re.I)
            for match in matches:
                duration = match
                # Validate that this looks like a reasonable duration
                if TimingUtils.is_valid_duration(duration):
                    logger.info(f"Found total duration in text: {duration}")
                    return duration

        return None
