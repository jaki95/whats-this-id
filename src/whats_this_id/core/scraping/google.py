import asyncio
import json
from typing import Optional
from urllib.parse import quote

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    CrawlerRunConfig,
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from whats_this_id.core.scraping.config import browser_config


async def extract_google_search_links(
    website: str, query: str, timeout: int = 30, max_retries: int = 3
) -> Optional[str]:
    """Return the first result URL from a Google search restricted to *website* containing *query*."""
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

    crawler = None
    for attempt in range(max_retries):
        try:
            crawler = AsyncWebCrawler(config=browser_config)

            await crawler.__aenter__()
            try:
                result = await asyncio.wait_for(
                    crawler.arun(url=search_url, config=config), timeout=timeout
                )

                if not result.success:
                    print(
                        f"Crawl failed (attempt {attempt + 1}): {result.error_message}"
                    )
                    if attempt == max_retries - 1:
                        return None
                    continue

                data = json.loads(result.extracted_content)
                print(f"Extracted {len(data)} search results")

                for entry in data:
                    if website in entry["link"]:
                        print(f"{entry['title']} -> {entry['link']}")
                        return entry["link"]

                print("No tracklist found")
                return None

            finally:
                # Ensure proper cleanup
                await crawler.__aexit__(None, None, None)

        except asyncio.TimeoutError:
            print(
                f"Search timed out after {timeout}s (attempt {attempt + 1}/{max_retries})"
            )
            if crawler:
                try:
                    await crawler.close()
                except Exception:
                    pass  # Ignore cleanup errors on timeout

            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1)

        except Exception as e:
            print(f"Search failed (attempt {attempt + 1}/{max_retries}): {e}")

            if crawler:
                try:
                    await crawler.close()
                except Exception:
                    pass  # Ignore cleanup errors

            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1)  # Brief delay before retry

    return None
