from crawl4ai import (
    AsyncWebCrawler,
)

from whats_this_id.core.config import BROWSER_CONFIG, CRAWLER_CONFIG


async def extract_tracklist(url: str) -> str:
    """Return a markdown version of the tracklist contained at *url*."""
    async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
        result = await crawler.arun(
            url=url,
            config=CRAWLER_CONFIG,
        )

        if result.success:
            return result.markdown
        else:
            print("Error:", result.error_message)
            return ""
