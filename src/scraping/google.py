import json
from urllib.parse import quote

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    CrawlerRunConfig,
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from scraping.config import browser_config


async def extract_google_search_links(website: str, query: str):
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

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=search_url, config=config)
        if not result.success:
            print("Crawl failed:", result.error_message)
            return
        data = json.loads(result.extracted_content)
        print(f"Extracted {len(data)} search results")
        for entry in data:
            if website in entry["link"]:
                print(f"{entry['title']} -> {entry['link']}")
                return entry["link"]
        print("No tracklist found")
        return None
