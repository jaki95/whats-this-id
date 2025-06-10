from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scraping.config import CONFIG_DIR

browser_config = BrowserConfig(
    headless=True,
    verbose=True,
    use_managed_browser=True,
    user_data_dir=(CONFIG_DIR / "browser_cache").as_posix(),  # using local browser cache to avoid captcha issues
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
