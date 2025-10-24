from typing import List

from dj_set_downloader import DomainTrack, DomainTracklist
from trackidnet import client

from whats_this_id.core.search.searcher import SearchResult, SearchStrategy


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

    def get_tracklist(self, slug: str) -> DomainTracklist:
        result = self.trackidnet.get_tracklist(slug)
        tracks = [
            DomainTrack(
                name=track.title,
                artist=track.artist,
                start_time=track.start_time,
                end_time=track.end_time,
            )
            for track in result.tracks
        ]
        return DomainTracklist(name=result.name, tracks=tracks)


if __name__ == "__main__":
    strategy = TrackIDNetSearchStrategy()
    result = strategy.search("mind against")
    slug = result[0].link
    tracklist = strategy.get_tracklist(slug)
    for track in tracklist.tracks:
        print(f"{track.name} - {track.artist} - {track.start_time} - {track.end_time}")
        print("--------------------------------")
