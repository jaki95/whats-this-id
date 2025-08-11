import asyncio
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from whats_this_id.core.scraping.google import GoogleHandler
from whats_this_id.core.scraping.tracklist import extract_tracklist


class FindTracklistInput(BaseModel):
    """Input schema for FindTracklist."""

    website: str = Field(..., description="The website to find the tracklist on")
    dj_set: str = Field(..., description="The DJ set to find the tracklist for")


class FindTracklist(BaseTool):
    name: str = "Find Tracklist"
    description: str = "Find the tracklist for a given DJ set on a given website"
    args_schema: Type[BaseModel] = FindTracklistInput
    google_handler: GoogleHandler = GoogleHandler()

    def _run(self, website: str, dj_set: str) -> str:
        async def async_find_tracklist():
            tracklist_url = await self.google_handler.search_for_tracklist_link(
                website, dj_set
            )
            if not tracklist_url:
                return ""
            return await extract_tracklist(tracklist_url)

        # Create a new event loop to avoid nested event loop issues
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_find_tracklist())
        finally:
            loop.close()
