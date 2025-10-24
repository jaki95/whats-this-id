"""
Example usage of the unified core module.
"""

from whats_this_id.core import TracklistManager


def main():
    """Example of using the unified core module."""
    # Initialize the manager
    manager = TracklistManager()

    # Search for a tracklist
    query = "mind against"
    tracklist = manager.run(query)

    track_count = len(tracklist.tracks)
    print(f"Found {track_count} tracks")

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
