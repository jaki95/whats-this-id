"""
Unified configuration for the core module.
"""

from pathlib import Path
from typing import Any, Dict

from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parents[3]
BROWSER_CACHE_DIR = (ROOT_DIR / "browser_cache").as_posix()

# Browser configuration
BROWSER_CONFIG = BrowserConfig(
    headless=True,
    verbose=False,
    use_managed_browser=True,
    user_data_dir=BROWSER_CACHE_DIR,
    browser_type="chromium",
    # Force fresh browser instance and handle dynamic content
    extra_args=[
        "--no-first-run",
        "--disable-dev-shm-usage",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
    ],
)

# Content filtering
PRUNE_FILTER = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",
    min_word_threshold=50,
)

# Crawler configuration
CRAWLER_CONFIG = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        options={
            "ignore_links": True,
        },
    ),
    remove_overlay_elements=True,
    page_timeout=30000,  # 30 seconds timeout
    delay_before_return_html=2.0,  # Wait 2 seconds before returning HTML
)

# Default operation settings
DEFAULT_TIMEOUT = 15  # Reduced from 30 to 15 seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1

# Search configuration
SEARCH_CONFIG = {
    "min_confidence_threshold": 0.5,
    "max_results_per_source": 10,
    "timeout": DEFAULT_TIMEOUT,
    "max_retries": DEFAULT_MAX_RETRIES,
}

# Google search schema
GOOGLE_SEARCH_SCHEMA = {
    "name": "Google Search Results",
    "baseSelector": "div.tF2Cxc",
    "fields": [
        {"name": "title", "selector": "h3", "type": "text"},
        {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
    ],
}
