import asyncio
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from whats_this_id.core.scrape.google import extract_google_search_links
from whats_this_id.core.scrape.tracklist import extract_tracklist


class FindTracklistInput(BaseModel):
    """Input schema for FindTracklist."""

    website: str = Field(..., description="The website to find the tracklist on")
    dj_set: str = Field(..., description="The DJ set to find the tracklist for")


class FindTracklist(BaseTool):
    name: str = "Find Tracklist"
    description: str = "Find the tracklist for a given DJ set on a given website"
    args_schema: Type[BaseModel] = FindTracklistInput

    def _run(self, website: str, dj_set: str) -> str:
        tracklist_url = asyncio.run(extract_google_search_links(website, dj_set))
        if not tracklist_url:
            return ""
        return asyncio.run(extract_tracklist(tracklist_url))
