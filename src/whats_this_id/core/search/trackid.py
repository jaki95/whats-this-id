from typing import List

from dj_set_downloader import DomainTrack, DomainTracklist
from trackidnet import client

from whats_this_id.core.parsers.timing_utils import TimingUtils
from whats_this_id.core.search.strategy import SearchResult, SearchStrategy


class TrackIDNetSearchStrategy(SearchStrategy):
    """Search strategy for finding tracklists on trackid.net."""

    def __init__(self):
        self.trackidnet = client.TrackIDNet()

    def search(self, query: str) -> List[SearchResult]:
        result = self.trackidnet.search_tracklist(query)
        return [
            SearchResult(link=result.slug, title=result.name)
            for result in result.results
        ]

    def get_tracklist(self, slug: str) -> tuple[DomainTracklist, str]:
        result = self.trackidnet.get_tracklist(slug)
        timing_utils = TimingUtils()
        tracks = [
            DomainTrack(
                track_number=i + 1,
                name=track.title,
                artist=track.artist,
                start_time=track.start_time,
                end_time=track.end_time,
            )
            for i, track in enumerate(result.tracks)
        ]
        # TODO: parse artist from name
        tracklist = DomainTracklist(name=result.name, tracks=tracks, artist="unknown")
        tracklist.tracks = timing_utils.apply_timing_rules(
            tracklist.tracks, result.duration
        )
        return tracklist, result.url


if __name__ == "__main__":
    strategy = TrackIDNetSearchStrategy()
    result = strategy.search("mind against")
    slug = result[0].link
    tracklist = strategy.get_tracklist(slug)
    for track in tracklist.tracks:
        print(f"{track.name} - {track.artist} - {track.start_time} - {track.end_time}")
        print("--------------------------------")
