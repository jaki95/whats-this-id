"""
Unified fetcher that handles all content fetching operations.
"""

import logging

from crawl4ai import AsyncWebCrawler

from whats_this_id.core.common import BaseOperation
from whats_this_id.core.config import BROWSER_CONFIG, CRAWLER_CONFIG
from whats_this_id.core.cookie_refresh import CookieRefreshService

logger = logging.getLogger(__name__)


class Fetcher(BaseOperation):
    """Unified fetcher that handles HTML content fetching."""

    def __init__(self, timeout: int = 30, max_retries: int = 1):  # Reduced to 1 retry
        super().__init__("Fetcher", timeout, max_retries)
        self.name = "html"
        self.content_type = "html"
        self.cookie_refresh_service = CookieRefreshService()

    async def _execute_async(self, url: str) -> str:
        """Fetch HTML content from the given URL."""
        try:
            async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CRAWLER_CONFIG,
                )

                if result.success:
                    return result.html
                else:
                    raise Exception(f"Failed to fetch content: {result.error_message}")

        except Exception as e:
            error_str = str(e)

            # Check for specific connection-related errors
            if any(
                conn_error in error_str.lower()
                for conn_error in [
                    "err_connection_closed",
                    "err_connection_refused",
                    "err_connection_timed_out",
                    "err_connection_reset",
                    "net::err_connection_closed",
                    "net::err_connection_refused",
                    "net::err_connection_timed_out",
                    "net::err_connection_reset",
                    "connection closed",
                    "connection refused",
                    "connection timed out",
                    "connection reset",
                ]
            ):
                # Try to refresh cookies if this appears to be a cookie-related issue
                logger.info(
                    f"Connection error detected for {url}, attempting cookie refresh..."
                )
                try:
                    cookies_refreshed = (
                        await self.cookie_refresh_service.refresh_cookies_if_needed(
                            error_str
                        )
                    )
                    if cookies_refreshed:
                        logger.info("✅ Cookies refreshed successfully")
                        raise Exception(
                            f"Unable to connect to {url}. Cookies have been refreshed - please retry the request."
                        )
                    else:
                        logger.warning("❌ Cookie refresh failed or was skipped")
                        # Provide manual instructions
                        manual_instructions = self.cookie_refresh_service._refresh_cookies_manual_instruction()
                        logger.info(manual_instructions)
                        raise Exception(
                            f"Unable to connect to {url}. The website may be blocking requests. Manual cookie refresh may be required."
                        )
                except Exception as refresh_error:
                    logger.warning(f"Cookie refresh failed: {refresh_error}")
                    raise Exception(
                        f"Unable to connect to {url}. The website may be temporarily unavailable or blocking requests."
                    )
            else:
                # Re-raise other errors as-is
                raise

    def fetch(self, url: str) -> str:
        """Synchronous fetch method for backward compatibility."""
        result = self.execute(url)
        return result.data if result.success else ""

    def supports(self, content_type: str) -> bool:
        """Check if this fetcher supports the given content type."""
        return content_type == self.content_type
