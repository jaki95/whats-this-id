"""
Unified manager that orchestrates all tracklist search operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from dj_set_downloader.models.domain_track import DomainTrack

from whats_this_id.core.common import DomainTracklist, SearchRun, log_step
from whats_this_id.core.config import SEARCH_CONFIG
from whats_this_id.core.fetchers.fetcher import Fetcher
from whats_this_id.core.parsers.parser import Parser
from whats_this_id.core.search.searcher import Searcher

logger = logging.getLogger(__name__)


class TracklistManager:
    """Manager for tracklist search operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**SEARCH_CONFIG, **(config or {})}

        # Initialize components
        self.fetcher = Fetcher(
            timeout=self.config.get("timeout", 30),
            max_retries=1,
        )
        self.parser = Parser(
            timeout=self.config.get("parser_timeout", 15),
            max_retries=1,
        )
        self.searcher = Searcher(
            timeout=self.config.get("timeout", 30),
            max_retries=1,
        )

        self.min_confidence_threshold = self.config.get("min_confidence_threshold", 0.5)

    def run(self, query: str) -> SearchRun:
        """Run a complete tracklist search operation."""
        start_time = datetime.now()
        run = SearchRun(query=query)

        try:
            # Validate input
            if not query or not query.strip():
                log_step(
                    run, "Validation", "Manager", "error", error="Query cannot be empty"
                )
                return run

            # Search for tracklists
            search_results = self._search_tracklists(query, run)

            # Fetch and parse content
            parsed_tracklists = self._fetch_and_parse(search_results, run)

            # Merge and deduplicate results
            self._merge_results(parsed_tracklists, run)

            if run.final_tracklist is not None:
                if (
                    hasattr(run.final_tracklist, "tracks")
                    and run.final_tracklist.tracks is not None
                ):
                    run.success = len(run.final_tracklist.tracks) > 0
                else:
                    run.success = False
            else:
                run.success = False

        except Exception as e:
            logger.error(f"Unexpected error in search run: {e}", exc_info=True)
            log_step(run, "Manager", "Manager", "error", error=str(e))
        finally:
            end_time = datetime.now()
            run.total_duration_ms = (end_time - start_time).total_seconds() * 1000

        return run

    def _search_tracklists(self, query: str, run: SearchRun) -> List[Any]:
        """Search for tracklists using the unified searcher."""
        step_start = datetime.now()

        try:
            # Search 1001tracklists
            results = self.searcher.search_tracklist1001(query)

            duration = (datetime.now() - step_start).total_seconds() * 1000
            log_step(
                run,
                "Search",
                "1001tracklists",
                "success" if results else "no_results",
                details=f"{len(results)} results found",
                duration_ms=duration,
            )
            logger.info(f"Search 1001tracklists: {len(results)} results")

            return results

        except Exception as e:
            duration = (datetime.now() - step_start).total_seconds() * 1000
            error_msg = str(e)

            if (
                "net::err_aborted" in error_msg.lower()
                or "err_aborted" in error_msg.lower()
            ):
                user_friendly_error = "Search service temporarily blocked. This is usually temporary - please try again in a few minutes."
            elif "unable to connect" in error_msg.lower():
                user_friendly_error = f"Search service unavailable: {error_msg}"
            elif "timeout" in error_msg.lower():
                user_friendly_error = f"Search request timed out: {error_msg}"
            elif "blocking requests" in error_msg.lower():
                user_friendly_error = "Website blocked our request. This might be temporary - please try again later."
            else:
                user_friendly_error = error_msg

            logger.error(f"Search error: {e}")
            log_step(
                run,
                "Search",
                "1001tracklists",
                "error",
                error=user_friendly_error,
                duration_ms=duration,
            )
            return []

    def _fetch_and_parse(self, results: List[Any], run: SearchRun) -> List[tuple]:
        """Fetch content and parse tracklists."""
        parsed_tracklists = []

        for result in results:
            step_start = datetime.now()

            try:
                # Fetch content
                content = self.fetcher.fetch(result.link)
                if not content:
                    continue

                # Parse content
                tracks, confidence, total_duration, metadata = self.parser.parse(
                    content
                )

                # Filter by confidence threshold
                if confidence >= self.min_confidence_threshold:
                    parsed_tracklists.append(
                        (tracks, confidence, total_duration, metadata)
                    )

                duration = (datetime.now() - step_start).total_seconds() * 1000
                log_step(
                    run,
                    "Parse",
                    "Fetcher + Parser",
                    "success" if tracks else "no_results",
                    found_tracks=len(tracks),
                    confidence=confidence,
                    link=result.link,
                    duration_ms=duration,
                )
                logger.info(
                    f"Parsed {len(tracks)} tracks with confidence {confidence:.2f}"
                )

            except Exception as e:
                duration = (datetime.now() - step_start).total_seconds() * 1000
                error_msg = str(e)

                # Provide more user-friendly error messages for common issues
                if "unable to connect" in error_msg.lower():
                    user_friendly_error = f"Connection failed: {error_msg}"
                elif "timeout" in error_msg.lower():
                    user_friendly_error = f"Request timed out: {error_msg}"
                elif "blocking requests" in error_msg.lower():
                    user_friendly_error = f"Website blocked request: {error_msg}"
                else:
                    user_friendly_error = error_msg

                logger.error(f"Parse error for {result.link}: {e}")
                log_step(
                    run,
                    "Parse",
                    "Fetcher + Parser",
                    "error",
                    error=user_friendly_error,
                    link=result.link,
                    duration_ms=duration,
                )

        return parsed_tracklists

    def _merge_results(self, parsed_tracklists: List[tuple], run: SearchRun) -> None:
        """Merge and deduplicate tracklists."""
        if not parsed_tracklists:
            log_step(
                run,
                "Aggregation",
                "Manager",
                "no_results",
                details="No tracklists to merge",
            )
            run.final_tracklist = DomainTracklist()
            return

        # Combine all tracks and deduplicate by title
        all_tracks: list[DomainTrack] = []
        total_confidence = 0.0
        total_duration = None
        best_metadata = {"name": None, "artist": None, "year": None, "genre": None}

        for tracks, confidence, duration, metadata in parsed_tracklists:
            all_tracks.extend(tracks)
            total_confidence += confidence
            # Use the first non-None duration found
            if total_duration is None and duration is not None:
                total_duration = duration
                logger.info(f"Found total duration: {total_duration}")

            # Use the best metadata found (prefer non-None values)
            for key in best_metadata:
                if best_metadata[key] is None and metadata.get(key) is not None:
                    best_metadata[key] = metadata[key]

        # Deduplicate tracks by title (case-insensitive)
        seen_titles = set()
        unique_tracks = []

        for track in all_tracks:
            title_lower = track.name.lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_tracks.append(track)

        # Sort by track number
        try:
            unique_tracks.sort(
                key=lambda t: getattr(t, "track_number", 999)
                if getattr(t, "track_number", None) is not None
                else 999
            )
        except Exception as e:
            logger.warning(f"Error sorting tracks: {e}, keeping original order")
            pass  # If sorting fails, keep original order

        # Reapply timing rules after sorting to fix end times
        if unique_tracks and hasattr(self.parser, "_apply_timing_rules"):
            logger.info(
                f"Reapplying timing rules with total_duration: {total_duration}"
            )
            unique_tracks = self.parser._apply_timing_rules(
                unique_tracks, total_duration
            )

        avg_confidence = (
            total_confidence / len(parsed_tracklists) if parsed_tracklists else 0.0
        )

        # Store the total duration in the run for later use
        if total_duration:
            run.total_duration_ms = self._duration_to_ms(total_duration)

        # Create DomainTracklist with extracted metadata
        tracklist_kwargs = {
            "domain": "1001tracklists.com",
            "tracks": unique_tracks,
            "confidence": avg_confidence,
        }

        # Add metadata if available
        if best_metadata["name"]:
            tracklist_kwargs["name"] = best_metadata["name"]
        if best_metadata["artist"]:
            tracklist_kwargs["artist"] = best_metadata["artist"]
        if best_metadata["year"]:
            tracklist_kwargs["year"] = best_metadata["year"]
        if best_metadata["genre"]:
            tracklist_kwargs["genre"] = best_metadata["genre"]

        run.final_tracklist = DomainTracklist(**tracklist_kwargs)

        log_step(
            run,
            "Aggregation",
            "Manager",
            "success",
            found_tracks=len(unique_tracks),
            confidence=avg_confidence,
            details=f"Merged {len(parsed_tracklists)} tracklists into {len(unique_tracks)} unique tracks",
        )

        logger.info(
            f"Aggregation complete: {len(unique_tracks)} unique tracks from {len(parsed_tracklists)} tracklists"
        )

    def _duration_to_ms(self, duration: str) -> float:
        """Convert duration string (hh:mm:ss or mm:ss) to milliseconds."""
        try:
            parts = duration.split(":")
            if len(parts) == 2:  # mm:ss
                minutes, seconds = int(parts[0]), int(parts[1])
                total_seconds = minutes * 60 + seconds
            elif len(parts) == 3:  # hh:mm:ss
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                total_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                return 0.0

            return total_seconds * 1000.0
        except (ValueError, AttributeError):
            return 0.0
