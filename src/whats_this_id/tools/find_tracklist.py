import asyncio
import json
from typing import Type
from urllib.parse import quote

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

browser_config = BrowserConfig(
    headless=True,
    verbose=True,
    use_managed_browser=True,
    user_data_dir="/Users/jaki/Projects/whats-this-id/src/whats_this_id/config/browser_cache",
    browser_type="chromium",
)

prune_filter = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",
    min_word_threshold=50,
)

crawler_config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        options={
            "ignore_links": True,
        },
    ),
    remove_overlay_elements=True,
)


async def extract_google_search_links(website: str, query: str):
    encoded_query = quote(f"site:{website} {query}")
    search_url = f"https://www.google.com/search?q={encoded_query}"

    # Google search results have links inside divs with class 'tF2Cxc'
    schema = {
        "name": "Google Search Results",
        "baseSelector": "div.tF2Cxc",
        "fields": [
            {"name": "title", "selector": "h3", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=search_url, config=config)
        if not result.success:
            print("Crawl failed:", result.error_message)
            return
        data = json.loads(result.extracted_content)
        print(f"Extracted {len(data)} search results")
        for entry in data:
            if website in entry["link"]:
                print(f"{entry['title']} -> {entry['link']}")
                return entry["link"]
        print("No tracklist found")
        return None


async def extract_tracklist(url: str) -> str:
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=crawler_config,
        )

        if result.success:
            return result.markdown
        else:
            print("Error:", result.error_message)
            return ""


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
