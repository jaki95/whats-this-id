from pathlib import Path

from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

ROOT_DIR = Path(__file__).resolve().parents[5]

BROWSER_CACHE_DIR = (ROOT_DIR / "browser_cache").as_posix()

browser_config = BrowserConfig(
    headless=True,
    verbose=True,
    use_managed_browser=True,
    user_data_dir=BROWSER_CACHE_DIR,
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
