"""Async search utilities for concurrent tracklist and SoundCloud searches."""

import asyncio
import concurrent.futures
from functools import partial

from whats_this_id.agents import TracklistSearchCrew
from whats_this_id.core.scraping.soundcloud import find_soundcloud_djset


async def search_tracklist_and_soundcloud(query_text: str):
    """Run tracklist search and SoundCloud search concurrently."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create partial function for the tracklist search
        tracklist_search = partial(
            lambda q: TracklistSearchCrew().crew().kickoff(inputs={"dj_set": q}),
            query_text.strip(),
        )

        # Submit tracklist search to thread pool
        loop = asyncio.get_event_loop()
        tracklist_future = loop.run_in_executor(executor, tracklist_search)
        
        # Run SoundCloud search directly as async
        soundcloud_future = find_soundcloud_djset(query_text)

        # Wait for both to complete
        tracklist_result, dj_set_url = await asyncio.gather(
            tracklist_future, soundcloud_future
        )

        return tracklist_result, dj_set_url


def search_tracklist_and_soundcloud_sync(query_text: str):
    """Synchronous wrapper for Streamlit compatibility."""
    def run_async():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(search_tracklist_and_soundcloud(query_text))
        finally:
            loop.close()
    
    # Run in a separate thread to avoid event loop conflicts
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_async)
        return future.result()
