"""
Example usage of the unified core module.
"""

from whats_this_id.core import SearchRun, TracklistManager


def main():
    """Example of using the unified core module."""
    # Initialize the manager
    manager = TracklistManager()

    # Search for a tracklist
    query = "mind against afterlife voyage"
    result: SearchRun = manager.run(query)

    # Check if search was successful
    if result.success and result.final_tracklist is not None:
        tracks = (
            result.final_tracklist.tracks
            if hasattr(result.final_tracklist, "tracks")
            and result.final_tracklist.tracks is not None
            else []
        )
        track_count = len(tracks)
        print(f"Found {track_count} tracks")
        print(f"Search completed in {result.total_duration_ms:.2f}ms")

        for track in tracks:
            track_num = (
                f"{track.track_number:02d}" if track.track_number is not None else "??"
            )
            start_time = track.start_time if track.start_time is not None else "??:??"
            end_time = track.end_time if track.end_time is not None else "??:??"
            print(
                f"[{track_num}] {start_time} - {end_time} - {track.artist} - {track.name}"
            )
    else:
        print("Search failed")
        for step in result.steps:
            if step.error:
                print(f"Error in {step.step_name}: {step.error}")


if __name__ == "__main__":
    main()