import asyncio
from pathlib import Path

from sclib import SoundcloudAPI

from whats_this_id.core.scraping.google import extract_google_search_links

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


async def find_soundcloud_djset(dj_set: str) -> str:
    """Return a SoundCloud URL for the given *dj_set* query."""
    soundcloud_url = await extract_google_search_links("soundcloud.com", dj_set)
    return soundcloud_url or ""


def download_soundcloud_djset(url: str) -> None:
    """Download the DJ set MP3 from *url* into the local `data/` directory."""
    api = SoundcloudAPI()
    track = api.resolve(url)
    filename = DATA_DIR / f"{track.title}.mp3"
    with open(filename, "wb+") as file:
        track.write_mp3_to(file)


if __name__ == "__main__":
    # Example usage
    async def main():
        soundcloud_url = await find_soundcloud_djset("dax j chlar stone")
        if soundcloud_url:
            download_soundcloud_djset(soundcloud_url)

    asyncio.run(main())
