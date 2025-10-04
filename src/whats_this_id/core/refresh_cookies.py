#!/usr/bin/env python3
"""
Manual cookie refresh utility for updating browser cookies when websites block requests.
"""
import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from whats_this_id.core.cookie_refresh import CookieRefreshService


async def main():
    """Main function for manual cookie refresh."""
    print("🍪 Cookie Refresh Utility")
    print("=" * 50)
    
    service = CookieRefreshService()
    
    # Show current status
    status = service.get_refresh_status()
    print(f"Browser cache directory: {status['browser_cache_dir']}")
    print(f"Last refresh: {status['time_since_refresh']:.1f} seconds ago")
    print(f"Can refresh: {status['can_refresh']}")
    print()
    
    # Target URLs for cookie refresh
    target_urls = [
        "https://www.1001tracklists.com",
        "https://www.google.com"
    ]
    
    print("Refreshing cookies for the following sites:")
    for url in target_urls:
        print(f"  - {url}")
    print()
    
    # Perform the refresh
    print("Starting cookie refresh...")
    success = await service._refresh_cookies_automated(target_urls)
    
    if success:
        print("✅ Cookie refresh completed successfully!")
        print("You can now retry your search operations.")
    else:
        print("❌ Automated cookie refresh failed.")
        print()
        print("Manual refresh instructions:")
        print(service._refresh_cookies_manual_instruction())


if __name__ == "__main__":
    asyncio.run(main())
