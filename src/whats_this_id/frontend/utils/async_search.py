"""Async search utilities for concurrent tracklist and SoundCloud searches."""

import asyncio
import concurrent.futures
from functools import partial
import logging

from whats_this_id.agents import TracklistSearchCrew
from whats_this_id.core.scraping.soundcloud import find_soundcloud_djset

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def search_tracklist_and_soundcloud(query_text: str):
    """Run tracklist search and SoundCloud search concurrently with proper error handling."""
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create partial function for the tracklist search
            tracklist_search = partial(
                lambda q: TracklistSearchCrew().crew().kickoff(inputs={"dj_set": q}),
                query_text.strip(),
            )

            # Submit tracklist search to thread pool
            loop = asyncio.get_event_loop()
            tracklist_future = loop.run_in_executor(executor, tracklist_search)
            
            # Run SoundCloud search directly as async with timeout
            soundcloud_future = asyncio.wait_for(
                find_soundcloud_djset(query_text), 
                timeout=60.0  # 60 second timeout
            )

            # Wait for both to complete with overall timeout
            try:
                tracklist_result, dj_set_url = await asyncio.wait_for(
                    asyncio.gather(tracklist_future, soundcloud_future, return_exceptions=True),
                    timeout=120.0  # 2 minute overall timeout
                )
                
                # Handle exceptions from either task
                if isinstance(tracklist_result, Exception):
                    logger.error(f"Tracklist search failed: {tracklist_result}")
                    tracklist_result = None
                    
                if isinstance(dj_set_url, Exception):
                    logger.error(f"SoundCloud search failed: {dj_set_url}")
                    dj_set_url = ""

                return tracklist_result, dj_set_url

            except asyncio.TimeoutError:
                logger.error("Search operations timed out")
                return None, ""
                
    except Exception as e:
        logger.error(f"Search failed with unexpected error: {e}")
        return None, ""


def search_tracklist_and_soundcloud_sync(query_text: str):
    """Synchronous wrapper for Streamlit compatibility with improved error handling."""
    def run_async():
        # Create a new event loop for this thread
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(search_tracklist_and_soundcloud(query_text))
        except Exception as e:
            logger.error(f"Async execution failed: {e}")
            return None, ""
        finally:
            if loop:
                try:
                    # Cancel all pending tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    
                    # Give tasks a chance to clean up
                    if pending:
                        loop.run_until_complete(
                            asyncio.wait_for(
                                asyncio.gather(*pending, return_exceptions=True),
                                timeout=5.0
                            )
                        )
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup warning: {cleanup_error}")
                finally:
                    loop.close()
    
    # Run in a separate thread to avoid event loop conflicts
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            # Add timeout to prevent hanging
            return future.result(timeout=180.0)  # 3 minute timeout
    except concurrent.futures.TimeoutError:
        logger.error("Synchronous search wrapper timed out")
        return None, ""
    except Exception as e:
        logger.error(f"Synchronous search wrapper failed: {e}")
        return None, ""
