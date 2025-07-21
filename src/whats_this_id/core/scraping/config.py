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
    verbose=False,  # Reduce verbose output to prevent spam
    use_managed_browser=True,
    user_data_dir=BROWSER_CACHE_DIR,
    browser_type="chromium",
    # Add browser arguments for stability
    browser_args=[
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-features=VizDisplayCompositor",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # Skip images for faster loading
        "--disable-javascript",  # Disable JS if not needed for basic HTML parsing
        "--no-first-run",
        "--disable-default-apps",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
    ],
    # Add timeouts
    page_timeout=30000,  # 30 seconds page timeout
    request_timeout=20000,  # 20 seconds request timeout
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
    # Add request timeout
    page_timeout=30000,
)
