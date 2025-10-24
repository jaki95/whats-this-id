"""
Unified configuration for the core module.
"""

from pathlib import Path

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
    # Initialize browser with proper context handling
    extra_args=[
        "--no-first-run",
        "--disable-dev-shm-usage",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-tools",
        "--disable-plugins",
        "--disable-images",
        "--disable-javascript",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-sync",
        "--metrics-recording-only",
        "--safebrowsing-disable-auto-update",
        "--disable-client-side-phishing-detection",
        "--disable-hang-monitor",
        "--disable-prompt-on-repost",
        "--disable-domain-reliability",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
