from whats_this_id.core.scraping.google import GoogleHandler


class SoundCloudHandler:
    """Handles SoundCloud DJ set URL finding."""

    DEFAULT_SEARCH_SITE = "soundcloud.com"

    def __init__(self):
        self.google_handler = GoogleHandler()

    async def find_dj_set_url(self, dj_set: str) -> str | None:
        """
        Find a SoundCloud URL for the given DJ set query.

        Args:
            dj_set: The search query for the DJ set

        Returns:
            SoundCloud URL if found, None otherwise
        """
        try:
            soundcloud_url = await self.google_handler.search_for_tracklist_link(
                self.DEFAULT_SEARCH_SITE, dj_set
            )
            return soundcloud_url
        except Exception as e:
            print(f"Error finding SoundCloud DJ set '{dj_set}': {e}")
            return None
