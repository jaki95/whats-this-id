"""
Unified fetcher that handles all content fetching operations.
"""

import logging

from crawl4ai import AsyncWebCrawler

from whats_this_id.core.common import BaseOperation
from whats_this_id.core.config import BROWSER_CONFIG, CRAWLER_CONFIG

logger = logging.getLogger(__name__)


class Fetcher(BaseOperation):
    """Unified fetcher that handles HTML content fetching."""

    def __init__(self, timeout: int = 30, max_retries: int = 1):
        super().__init__("Fetcher", timeout, max_retries)
        self.name = "html"
        self.content_type = "html"

    async def _execute_async(self, url: str) -> str:
        """Fetch HTML content from the given URL."""
        try:
            async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CRAWLER_CONFIG,
                )

                if result.success:
                    return result.html
                else:
                    raise Exception(f"Failed to fetch content: {result.error_message}")

        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {e}")
            raise

    def fetch(self, url: str) -> str:
        """Synchronous fetch method for backward compatibility."""
        result = self.execute(url)
        return result.data if result.success else ""

    def supports(self, content_type: str) -> bool:
        """Check if this fetcher supports the given content type."""
        return content_type == self.content_type
