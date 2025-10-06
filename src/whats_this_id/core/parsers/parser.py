"""
Parser that handles all content parsing operations.
"""

import asyncio
import re
from typing import Any

from bs4 import BeautifulSoup

from whats_this_id.core.common import BaseOperation, DomainTrack, logger
from whats_this_id.core.parsers.metadata_extractor import MetadataExtractor
from whats_this_id.core.parsers.timing_utils import TimingUtils
from whats_this_id.core.parsers.track_extractors import TrackExtractors


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
            metadata = MetadataExtractor.extract_dj_set_metadata(soup)
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
            ("tlpItem elements", lambda: TrackExtractors.extract_from_tlp_items(soup)),
            (
                "track elements",
                lambda: TrackExtractors.extract_from_track_elements(soup),
            ),
            ("tlp ID elements", lambda: TrackExtractors.extract_from_tlp_ids(soup)),
            ("text patterns", lambda: TrackExtractors.extract_from_text_patterns(soup)),
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
        tracks = TimingUtils.apply_timing_rules(tracks, total_duration)

        return tracks

    def _extract_total_duration(self, soup: BeautifulSoup) -> str | None:
        """Extract the total duration of the DJ set from the 1001tracklists page."""
        # Get all text content for comprehensive search
        all_text = soup.get_text()

        # Debug: Log a sample of the HTML content to understand the structure
        logger.debug(f"HTML content sample: {all_text[:500]}...")

        # Try text-based extraction first
        duration = TimingUtils.extract_total_duration_from_text(all_text)
        if duration:
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
                    if TimingUtils.is_valid_duration(duration):
                        logger.info(f"Found total duration in element: {duration}")
                        return duration

        # If no duration found, return None
        logger.warning("Could not extract total duration from page")
        return None
