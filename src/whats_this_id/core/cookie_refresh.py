"""
Cookie refresh service for handling session updates when websites block requests.
"""

import asyncio
import logging
import time
from typing import List, Optional

from crawl4ai import AsyncWebCrawler

from whats_this_id.core.config import BROWSER_CACHE_DIR

logger = logging.getLogger(__name__)


class CookieRefreshService:
    """Service for refreshing cookies when websites block requests."""

    def __init__(self, browser_cache_dir: str = BROWSER_CACHE_DIR):
        self.browser_cache_dir = browser_cache_dir
        self.last_refresh_time = 0
        self.refresh_cooldown = 60  # 1 minute cooldown between refreshes (reduced)

    def _is_cookie_related_error(self, error_message: str) -> bool:
        """Check if the error is likely related to cookies/session issues."""
        error_lower = error_message.lower()

        # Common indicators of cookie/session issues
        cookie_indicators = [
            "err_connection_closed",
            "err_connection_refused",
            "err_connection_timed_out",
            "err_connection_reset",
            "net::err_connection_closed",
            "net::err_connection_refused",
            "net::err_connection_timed_out",
            "net::err_connection_reset",
            "blocking requests",
            "temporarily unavailable",
            "access denied",
            "forbidden",
            "unauthorized",
            "session expired",
            "login required",
            "connection closed",
            "connection refused",
            "connection timed out",
            "connection reset",
        ]

        return any(indicator in error_lower for indicator in cookie_indicators)

    def _should_refresh_cookies(self) -> bool:
        """Check if enough time has passed since last refresh."""
        current_time = time.time()
        return (current_time - self.last_refresh_time) > self.refresh_cooldown

    async def _refresh_cookies_automated(self, target_urls: List[str]) -> bool:
        """Automatically refresh cookies by visiting target websites."""
        try:
            logger.info("Starting automated cookie refresh...")

            # Try with headless mode first (more reliable)
            from crawl4ai import BrowserConfig, CrawlerRunConfig

            refresh_config = BrowserConfig(
                headless=True,  # Use headless for better reliability
                verbose=False,
                use_managed_browser=True,
                user_data_dir=self.browser_cache_dir,
                browser_type="chromium",
            )

            # Use a more permissive crawler config for cookie refresh
            crawler_config = CrawlerRunConfig(
                page_timeout=30000,  # Reasonable timeout
                wait_for="domcontentloaded",  # Less strict than networkidle
            )

            success_count = 0
            async with AsyncWebCrawler(config=refresh_config) as crawler:
                for url in target_urls:
                    try:
                        logger.info(f"Refreshing cookies for: {url}")
                        result = await crawler.arun(url=url, config=crawler_config)

                        if result.success:
                            logger.info(f"Successfully refreshed cookies for {url}")
                            success_count += 1
                        else:
                            logger.warning(
                                f"Failed to refresh cookies for {url}: {result.error_message}"
                            )

                    except Exception as e:
                        logger.warning(f"Error refreshing cookies for {url}: {e}")
                        continue

            # Consider it successful if we got at least one site working
            if success_count > 0:
                self.last_refresh_time = time.time()
                logger.info(
                    f"Cookie refresh completed successfully for {success_count}/{len(target_urls)} sites"
                )
                return True
            else:
                logger.warning("No sites were successfully refreshed")
                return False

        except Exception as e:
            logger.error(f"Failed to refresh cookies automatically: {e}")
            return False

    def _refresh_cookies_manual_instruction(self) -> str:
        """Provide manual instructions for cookie refresh."""
        instruction = f"""
🍪 Manual Cookie Refresh Instructions
=====================================

The automated cookie refresh failed. Please follow these steps to manually refresh your cookies:

1. Open a Chromium-based browser with the following command:
   # Try one of these commands (use whichever works on your system):
   chromium --user-data-dir="{self.browser_cache_dir}" --no-first-run
   # OR
   google-chrome --user-data-dir="{self.browser_cache_dir}" --no-first-run
   # OR
   chromium-browser --user-data-dir="{self.browser_cache_dir}" --no-first-run

2. Navigate to these websites in order:
   - https://www.1001tracklists.com
   - https://www.google.com

3. Complete any required authentication, captcha, or consent dialogs

4. Wait for each page to fully load

5. Close the browser completely

6. Retry your search operation

Browser cache directory: {self.browser_cache_dir}

Alternative: You can also run the cookie refresh utility:
   python src/whats_this_id/core/refresh_cookies.py
   
Or use the shell script (recommended):
   ./refresh_cookies.sh
        """
        return instruction

    async def refresh_cookies_if_needed(
        self, error_message: str, target_urls: Optional[List[str]] = None
    ) -> bool:
        """
        Refresh cookies if the error appears to be cookie-related and enough time has passed.

        Args:
            error_message: The error message that triggered the refresh check
            target_urls: List of URLs to visit for cookie refresh (defaults to 1001tracklists)

        Returns:
            True if cookies were refreshed, False otherwise
        """
        if not self._is_cookie_related_error(error_message):
            logger.debug("Error does not appear to be cookie-related, skipping refresh")
            return False

        if not self._should_refresh_cookies():
            logger.info("Cookie refresh on cooldown, skipping")
            return False

        # Default target URLs for cookie refresh
        if target_urls is None:
            target_urls = ["https://www.1001tracklists.com", "https://www.google.com"]

        logger.info("Cookie-related error detected, attempting refresh...")

        # Try automated refresh first
        success = await self._refresh_cookies_automated(target_urls)

        if not success:
            # If automated refresh fails, provide manual instructions
            logger.warning("Automated cookie refresh failed")
            instruction = self._refresh_cookies_manual_instruction()
            logger.info(instruction)
            return False

        return True

    def get_refresh_status(self) -> dict:
        """Get the current status of the cookie refresh service."""
        current_time = time.time()
        time_since_refresh = current_time - self.last_refresh_time
        can_refresh = time_since_refresh > self.refresh_cooldown

        return {
            "last_refresh_time": self.last_refresh_time,
            "time_since_refresh": time_since_refresh,
            "can_refresh": can_refresh,
            "refresh_cooldown": self.refresh_cooldown,
            "browser_cache_dir": self.browser_cache_dir,
        }
