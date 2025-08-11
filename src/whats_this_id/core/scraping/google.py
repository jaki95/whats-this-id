import asyncio
import json
from urllib.parse import quote

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    CrawlerRunConfig,
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from whats_this_id.core.scraping.config import browser_config


class GoogleSearchResult:
    """Represents a single Google search result."""

    def __init__(self, title: str, link: str):
        self.title = title
        self.link = link


class GoogleHandler:
    """Handles Google search operations with site restrictions."""

    # Search result schema for Google
    SEARCH_SCHEMA = {
        "name": "Google Search Results",
        "baseSelector": "div.tF2Cxc",
        "fields": [
            {"name": "title", "selector": "h3", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
        ],
    }

    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(
        self, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES
    ):
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_search_url(self, website: str, query: str) -> str:
        """Build Google search URL with site restriction."""
        encoded_query = quote(f"site:{website} {query}")
        return f"https://www.google.com/search?q={encoded_query}"

    def _create_crawler_config(self) -> CrawlerRunConfig:
        """Create crawler configuration for Google search."""
        extraction_strategy = JsonCssExtractionStrategy(
            self.SEARCH_SCHEMA, verbose=True
        )
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
        )

    def _parse_search_results(self, extracted_content: str) -> list[GoogleSearchResult]:
        """Parse extracted content into search results."""
        try:
            data = json.loads(extracted_content)
            return [
                GoogleSearchResult(title=entry["title"], link=entry["link"])
                for entry in data
                if "title" in entry and "link" in entry
            ]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse search results: {e}")
            return []

    def _find_matching_result(
        self, results: list[GoogleSearchResult], website: str
    ) -> str | None:
        """Find the first result that matches the target website."""
        for result in results:
            if website in result.link:
                print(f"{result.title} -> {result.link}")
                return result.link
        return None

    async def _perform_single_search(
        self, search_url: str, config: CrawlerRunConfig
    ) -> list[GoogleSearchResult] | None:
        """Perform a single search attempt."""
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await asyncio.wait_for(
                crawler.arun(url=search_url, config=config), timeout=self.timeout
            )

            if not result.success:
                print(f"Crawl failed: {result.error_message}")
                return None

            results = self._parse_search_results(result.extracted_content)
            print(f"Extracted {len(results)} search results")
            return results

    async def search_for_tracklist_link(self, website: str, query: str) -> str | None:
        """
        Search for a tracklist link on a specific website.

        Args:
            website: The target website to search within
            query: The search query terms

        Returns:
            The first matching URL, or None if not found
        """
        search_url = self._build_search_url(website, query)
        config = self._create_crawler_config()

        for attempt in range(self.max_retries):
            try:
                results = await self._perform_single_search(search_url, config)

                if results is None:
                    if attempt == self.max_retries - 1:
                        return None
                    continue

                # Look for matching result
                matching_link = self._find_matching_result(results, website)
                if matching_link:
                    return matching_link

                print("No tracklist found")
                return None

            except asyncio.TimeoutError:
                print(
                    f"Search timed out after {self.timeout}s (attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAY)

            except Exception as e:
                print(f"Search failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAY)

        return None
