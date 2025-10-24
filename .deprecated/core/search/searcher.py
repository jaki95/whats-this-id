"""
Search strategies and result models.
"""

import json
from abc import ABC, abstractmethod
from typing import List, Optional
from urllib.parse import quote

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from whats_this_id.core.common import BaseOperation
from whats_this_id.core.config import BROWSER_CONFIG, GOOGLE_SEARCH_SCHEMA


class SearchResult:
    """Represents a single search result."""

    def __init__(self, link: str, title: str, snippet: str = ""):
        self.link = link
        self.title = title
        self.snippet = snippet


class SearchStrategy(ABC):
    """Abstract base class for search strategies."""

    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        """Search for tracklists using the given query."""
        pass


class Searcher(BaseOperation):
    """Unified search that handles Google searches with site restrictions."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        super().__init__("Searcher", timeout, max_retries)

    def _build_search_url(self, website: str, query: str) -> str:
        """Build Google search URL with site restriction."""
        encoded_query = quote(f"site:{website} {query}")
        return f"https://www.google.com/search?q={encoded_query}"

    def _create_crawler_config(self) -> CrawlerRunConfig:
        """Create crawler configuration for Google search."""
        extraction_strategy = JsonCssExtractionStrategy(
            GOOGLE_SEARCH_SCHEMA, verbose=True
        )
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
        )

    def _parse_search_results(self, extracted_content: str) -> List[SearchResult]:
        """Parse extracted content into search results."""
        try:
            data = json.loads(extracted_content)
            results = [
                SearchResult(
                    link=entry.get("link", ""), title=entry.get("title", ""), snippet=""
                )
                for entry in data
                if "title" in entry and "link" in entry
            ]
            return results
        except (json.JSONDecodeError, KeyError) as e:
            raise Exception(f"Failed to parse search results: {e}")

    def _find_matching_result(
        self, results: List[SearchResult], website: str
    ) -> Optional[str]:
        """Find the first result that matches the target website."""
        for result in results:
            if website in result.link:
                return result.link
        return None

    async def _execute_async(self, website: str, query: str) -> Optional[str]:
        """Search for a tracklist link on a specific website."""
        search_url = self._build_search_url(website, query)
        config = self._create_crawler_config()

        try:
            async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
                result = await crawler.arun(url=search_url, config=config)

                if not result.success:
                    raise Exception(f"Search failed: {result.error_message}")

                results = self._parse_search_results(result.extracted_content)
                return self._find_matching_result(results, website)
        except Exception as e:
            error_msg = str(e)
            # Handle the specific crawl4ai managed browser error
            if (
                "list index out of range" in error_msg
                and "context.pages[0]" in error_msg
            ):
                # Retry with a fresh browser instance
                from crawl4ai import BrowserConfig

                temp_config = BrowserConfig(
                    headless=True,
                    verbose=False,
                    use_managed_browser=False,  # Temporarily disable for retry
                    browser_type="chromium",
                )
                async with AsyncWebCrawler(config=temp_config) as crawler:
                    result = await crawler.arun(url=search_url, config=config)
                    if not result.success:
                        raise Exception(f"Search failed: {result.error_message}")
                    results = self._parse_search_results(result.extracted_content)
                    return self._find_matching_result(results, website)
            else:
                raise

    def search_for_tracklist_link(self, website: str, query: str) -> Optional[str]:
        """Synchronous method for backward compatibility."""
        result = self.execute(website, query)
        return result.data if result.success else None

    def search_tracklist1001(self, query: str) -> List[SearchResult]:
        """Search for tracklists on 1001tracklists.com."""
        result = self.execute("1001tracklists.com", query)

        if result.success and result.data:
            return [
                SearchResult(
                    link=result.data,
                    title=f"Tracklist: {query}",
                    snippet="Found tracklist on 1001tracklists.com",
                )
            ]
        return []
