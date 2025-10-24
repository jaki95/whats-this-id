"""
Example usage of the core tracklist orchestrator.
"""

from whats_this_id.core.orchestration.orchestrator import Orchestrator


def main():
    # Initialize the orchestrator
    orchestrator = Orchestrator()

    # Search for a tracklist
    query = "Bassiani invites Chlär"
    tracklist, url = orchestrator.run(query)

    track_count = len(tracklist.tracks)
    print(f"Found {track_count} tracks")
    print(f"Soundcloud URL: {url}")

    for track in tracklist.tracks:
        track_num = (
            f"{track.track_number:02d}" if track.track_number is not None else "??"
        )
        start_time = track.start_time if track.start_time is not None else "??:??"
        end_time = track.end_time if track.end_time is not None else "??:??"
        print(
            f"[{track_num}] {start_time} - {end_time} - {track.artist} - {track.name}"
        )


if __name__ == "__main__":
    main()
