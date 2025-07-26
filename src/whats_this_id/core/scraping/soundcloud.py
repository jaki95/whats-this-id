from pathlib import Path

from sclib import SoundcloudAPI

from whats_this_id.core.scraping.google import extract_google_search_links

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


class SoundCloudHandler:
    """Handles SoundCloud DJ set search."""

    DEFAULT_SEARCH_SITE = "soundcloud.com"

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self._api: SoundcloudAPI | None = None

    @property
    def api(self) -> SoundcloudAPI:
        """Lazy-load the SoundCloud API instance."""
        if self._api is None:
            self._api = SoundcloudAPI()
        return self._api

    async def find_dj_set_url(self, dj_set: str) -> str | None:
        """
        Find a SoundCloud URL for the given DJ set query.

        Args:
            dj_set: The search query for the DJ set

        Returns:
            SoundCloud URL if found, None otherwise
        """
        try:
            soundcloud_url = await extract_google_search_links(
                self.DEFAULT_SEARCH_SITE, dj_set
            )
            return soundcloud_url
        except Exception as e:
            print(f"Error finding SoundCloud DJ set '{dj_set}': {e}")
            return None
