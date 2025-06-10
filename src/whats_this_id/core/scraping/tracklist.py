from crawl4ai import (
    AsyncWebCrawler,
)

from whats_this_id.core.scraping.config import browser_config, crawler_config


async def extract_tracklist(url: str) -> str:
    """Return a markdown version of the tracklist contained at *url*."""
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