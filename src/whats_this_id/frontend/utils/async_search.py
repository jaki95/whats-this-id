"""Async search utilities for concurrent tracklist and SoundCloud searches."""

import asyncio
import concurrent.futures
from functools import partial

from whats_this_id.agents import TracklistSearchCrew
from whats_this_id.core.scraping.soundcloud import find_soundcloud_djset


async def search_tracklist_and_soundcloud(query_text: str):
    """Run tracklist search and SoundCloud search concurrently."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create partial functions for the searches
        tracklist_search = partial(
            lambda q: TracklistSearchCrew().crew().kickoff(inputs={"dj_set": q}),
            query_text.strip()
        )
        soundcloud_search = partial(find_soundcloud_djset, query_text)
        
        # Submit both tasks to run concurrently
        loop = asyncio.get_event_loop()
        tracklist_future = loop.run_in_executor(executor, tracklist_search)
        soundcloud_future = loop.run_in_executor(executor, soundcloud_search)
        
        # Wait for both to complete
        tracklist_result, dj_set_url = await asyncio.gather(
            tracklist_future, soundcloud_future
        )
        
        return tracklist_result, dj_set_url 