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
        total_duration: str | None = None,
    ) -> list[DomainTrack]:
        """
        Apply timing rules to a list of tracks.
        """
        if not tracks:
            return tracks

        logger.info(
            f"Applying timing rules to {len(tracks)} tracks (total_duration={total_duration})"
        )

        # Sort and deduplicate
        tracks = sorted(tracks, key=lambda t: self.parse_time(t.start_time))
        tracks = self._deduplicate_tracks(tracks)

        # Add intro "ID - ID" if needed
        tracks = self._add_intro_track(tracks)

        # Set missing end times
        for i, track in enumerate(tracks):
            if not track.end_time:
                if i < len(tracks) - 1:
                    track.end_time = tracks[i + 1].start_time
                    logger.debug(f"Filled missing end_time for track {i + 1}")
                elif total_duration:
                    track.end_time = total_duration
                    logger.debug("Filled last track end_time from total_duration")

        # Process gaps between tracks
        tracks = self._process_gaps(tracks)

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

    def _add_intro_track(self, tracks: list[DomainTrack]) -> list[DomainTrack]:
        if not tracks or self.parse_time(tracks[0].start_time) == timedelta(seconds=0):
            return tracks

        first_start = self.parse_time(tracks[0].start_time)
        if first_start > timedelta(seconds=0):
            intro_track = DomainTrack(
                track_number=None,
                name="ID",
                artist="ID",
                start_time=self.format_time(timedelta(seconds=0)),
                end_time=self.format_time(first_start),
            )
            tracks.insert(0, intro_track)
            logger.debug(f"Inserted intro ID track: 00:00 -> {intro_track.end_time}")
        return tracks

    def _process_gaps(
        self, tracks: list[DomainTrack], min_gap: timedelta = timedelta(seconds=60)
    ) -> list[DomainTrack]:
        """
        Process gaps between tracks.
        If the gap is longer than min_gap, insert an ID track.
        If the gap is shorter than min_gap, adjust the previous
        end time and the next start time to the midpoint of the gap.
        """
        adjusted_tracks = []

        for i, track in enumerate(tracks):
            start = self.parse_time(track.start_time)
            end = self.parse_time(track.end_time) if track.end_time else start
            adjusted_tracks.append(track)

            if i == len(tracks) - 1:
                continue  # skip last, handled later

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
