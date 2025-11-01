"""
Timing utilities for parsing, formatting, and adjusting track timings.
"""

import logging
from datetime import timedelta

from dj_set_downloader import DomainTrack

logger = logging.getLogger(__name__)


class TimingUtils:
    """Utility class for handling timing operations and track alignment."""

    def parse_time(self, t: str) -> timedelta:
        """Convert 'H:MM:SS' or 'MM:SS' string to timedelta."""
        if not t:
            raise ValueError("Empty time string")

        # Remove fractional seconds by splitting on '.' and taking the first part
        t = t.split(".")[0]
        parts = [int(x) for x in t.split(":")]

        if len(parts) == 2:
            return timedelta(minutes=parts[0], seconds=parts[1])
        if len(parts) == 3:
            return timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])

        raise ValueError(f"Invalid time format: {t}")

    def format_time(self, td: timedelta) -> str:
        """Convert timedelta to 'HH:MM:SS' format."""
        total_seconds = int(td.total_seconds())
        h, remainder = divmod(total_seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def apply_timing_rules(
        self,
        tracks: list[DomainTrack],
        total_duration: timedelta,
        intro_outro_threshold: timedelta = timedelta(seconds=30),
        min_gap_threshold: timedelta = timedelta(seconds=60),
    ) -> list[DomainTrack]:
        """
        Apply timing rules to a list of tracks.

        Args:
            tracks: List of domain tracks to process.
            total_duration: Total duration of the tracklist.
            intro_outro_threshold: Threshold for adding intro/outro tracks.
                If gap is <= threshold, extend the track; if > threshold, add ID track.
                Defaults to 30 seconds.
            min_gap_threshold: Minimum gap between tracks to insert an ID track.
                Gaps <= this threshold will be adjusted to midpoint.
                Defaults to 60 seconds.

        Returns:
            Processed list of tracks with timing rules applied.
        """
        if not tracks:
            return tracks

        logger.info(
            f"Applying timing rules to {len(tracks)} tracks "
            f"(total_duration={total_duration}, "
            f"intro_outro_threshold={intro_outro_threshold}, "
            f"min_gap_threshold={min_gap_threshold})"
        )

        # Sort and deduplicate
        tracks = sorted(tracks, key=lambda t: self.parse_time(t.start_time))
        tracks = self._deduplicate_tracks(tracks)

        # Add intro ID track if needed
        tracks = self._add_intro_track(tracks, threshold=intro_outro_threshold)

        # Process gaps between tracks
        tracks = self._process_gaps(tracks, min_gap=min_gap_threshold)

        # Add outro track if needed (handles missing end_time for last track)
        tracks = self._add_outro_track(
            tracks, total_duration, threshold=intro_outro_threshold
        )

        # Renumber sequentially
        for i, track in enumerate(tracks, start=1):
            track.track_number = i

        # Normalise all time strings to HH:MM:SS format
        for track in tracks:
            if track.start_time:
                track.start_time = self.format_time(self.parse_time(track.start_time))
            if track.end_time:
                track.end_time = self.format_time(self.parse_time(track.end_time))

        return tracks

    def _deduplicate_tracks(self, tracks: list[DomainTrack]) -> list[DomainTrack]:
        """Remove duplicate tracks (same artist + title), merging timing ranges."""
        if not tracks:
            return tracks

        seen: dict[tuple[str, str], DomainTrack] = {}
        deduped: list[DomainTrack] = []

        for track in tracks:
            key = (track.artist.lower().strip(), track.name.lower().strip())

            if key not in seen:
                seen[key] = track
                deduped.append(track)
                continue

            existing = seen[key]
            existing_start = self.parse_time(existing.start_time)
            existing_end = (
                self.parse_time(existing.end_time)
                if existing.end_time
                else existing_start
            )
            current_start = self.parse_time(track.start_time)
            current_end = (
                self.parse_time(track.end_time) if track.end_time else current_start
            )

            merged_start = min(existing_start, current_start)
            merged_end = max(existing_end, current_end)
            existing.start_time = self.format_time(merged_start)
            existing.end_time = self.format_time(merged_end)

            logger.debug(
                f"Merged duplicate track: {track.artist} - {track.name} "
                f"({existing.start_time} -> {existing.end_time})"
            )

        return deduped

    def _add_intro_track(
        self, tracks: list[DomainTrack], threshold: timedelta = timedelta(seconds=30)
    ) -> list[DomainTrack]:
        """
        Add an intro track if the first track starts after the threshold.
        Otherwise, edit the first track to start at 00:00:00.
        """
        if not tracks or self.parse_time(tracks[0].start_time) < threshold:
            tracks[0].start_time = self.format_time(timedelta(seconds=0))
            return tracks

        intro_track = DomainTrack(
            name="ID",
            artist="ID",
            start_time=self.format_time(timedelta(seconds=0)),
            end_time=tracks[0].start_time,
        )
        tracks.insert(0, intro_track)
        logger.debug(f"Inserted intro ID track: 00:00 -> {intro_track.end_time}")
        return tracks

    def _add_outro_track(
        self,
        tracks: list[DomainTrack],
        total_duration: timedelta,
        threshold: timedelta = timedelta(seconds=30),
    ) -> list[DomainTrack]:
        """
        Add an outro track if the last track ends before the total duration
        the difference is greater than the threshold.
        Otherwise, edit the last track to end at the total duration.
        Handles missing end_time for the last track by setting it to total_duration.
        """
        if not tracks:
            return tracks

        if not tracks[-1].end_time:
            tracks[-1].end_time = self.format_time(total_duration)
            logger.debug("Filled last track end_time from total_duration")
            return tracks

        last_end = self.parse_time(tracks[-1].end_time)
        if last_end >= total_duration:
            return tracks

        if last_end + threshold >= total_duration:
            tracks[-1].end_time = self.format_time(total_duration)
            return tracks

        outro_track = DomainTrack(
            name="ID",
            artist="ID",
            start_time=self.format_time(last_end),
            end_time=self.format_time(total_duration),
        )
        tracks.append(outro_track)
        logger.debug(
            f"Inserted outro ID track: {outro_track.start_time} -> {outro_track.end_time}"
        )
        return tracks

    def _process_gaps(
        self, tracks: list[DomainTrack], min_gap: timedelta = timedelta(seconds=60)
    ) -> list[DomainTrack]:
        """
        Process gaps between tracks.
        Sets missing end_times for tracks based on the next track's start_time.
        If the gap is longer than min_gap, insert an ID track.
        If the gap is shorter than min_gap, adjust the previous
        end time and the next start time to the midpoint of the gap.
        """
        adjusted_tracks = []

        for i, track in enumerate(tracks):
            # Set missing end_time
            if not track.end_time and i < len(tracks) - 1:
                track.end_time = tracks[i + 1].start_time
                logger.debug(f"Filled missing end_time for track {i + 1}")

            adjusted_tracks.append(track)

            if i == len(tracks) - 1:
                # Last track, no gap to process
                continue

            start = self.parse_time(track.start_time)
            end = self.parse_time(track.end_time) if track.end_time else start
            next_track = tracks[i + 1]
            next_start = self.parse_time(next_track.start_time)
            gap = next_start - end

            if gap < timedelta(seconds=0):
                logger.warning(
                    f"Overlap detected: {track.artist} → {next_track.artist} ({abs(gap)} overlap)"
                )
                continue

            if gap > min_gap:
                # Insert ID track for long gap
                id_track = DomainTrack(
                    track_number=None,
                    name="ID",
                    artist="ID",
                    start_time=self.format_time(end),
                    end_time=self.format_time(next_start),
                )
                adjusted_tracks.append(id_track)
                logger.debug(
                    f"Inserted gap ID track: {id_track.start_time} → {id_track.end_time} (gap={gap})"
                )

            elif gap > timedelta(seconds=0):
                midpoint = end + gap / 2
                midpoint_str = self.format_time(midpoint)

                # Adjust previous end & next start
                adjusted_tracks[-1].end_time = midpoint_str
                next_track.start_time = midpoint_str
                logger.debug(
                    f"Adjusted short gap ({gap}): midpoint {midpoint_str} "
                    f"between '{track.name}' and '{next_track.name}'"
                )

        return adjusted_tracks
