"""
HTML fetcher implementation.
"""

import asyncio

from crawl4ai import AsyncWebCrawler

from whats_this_id.core.config import BROWSER_CONFIG, CRAWLER_CONFIG

from .base import Fetcher

browser_config = BROWSER_CONFIG
crawler_config = CRAWLER_CONFIG


class HTMLFetcher(Fetcher):
    """Fetcher for HTML content."""

    def __init__(self):
        self.name = "html"
        self.content_type = "html"

    def fetch(self, url: str) -> str:
        """Fetch HTML content from the given URL."""
        try:
            # Run the async fetch in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._async_fetch(url))
            finally:
                loop.close()
            return result
        except Exception:
            return ""

    async def _async_fetch(self, url: str) -> str:
        """Internal async fetch method."""
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=crawler_config,
                )

                if result.success:
                    return result.html
                else:
                    return ""
        except Exception:
            return ""

    def supports(self, content_type: str) -> bool:
        """Check if this fetcher supports the given content type."""
        return content_type == self.content_type
