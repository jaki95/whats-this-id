from datetime import timedelta

import pytest
from dj_set_downloader import DomainTrack

from whats_this_id.core.parsers.timing_utils import TimingUtils


@pytest.mark.parametrize(
    "time_str,expected",
    [
        ("00:00:00", timedelta(seconds=0)),
        ("00:00:01", timedelta(seconds=1)),
        ("00:01:00", timedelta(minutes=1)),
        ("01:00:00", timedelta(hours=1)),
        ("01:01:00.9", timedelta(hours=1, minutes=1)),
        ("01:01:01", timedelta(hours=1, minutes=1, seconds=1)),
    ],
)
def test_parse_time(time_str, expected):
    timing_utils = TimingUtils()
    assert timing_utils.parse_time(time_str) == expected


@pytest.mark.parametrize(
    "time_str",
    [
        "00:00:00:00",
        "",
        "invalid",
    ],
)
def test_parse_time_invalid(time_str):
    timing_utils = TimingUtils()
    with pytest.raises(ValueError):
        timing_utils.parse_time(time_str)


@pytest.mark.parametrize(
    "timedelta_obj,expected",
    [
        (timedelta(seconds=0), "00:00:00"),
        (timedelta(seconds=1), "00:00:01"),
        (timedelta(minutes=1), "00:01:00"),
        (timedelta(hours=1), "01:00:00"),
        (timedelta(hours=1, minutes=1), "01:01:00"),
        (timedelta(hours=1, minutes=1, seconds=1), "01:01:01"),
    ],
)
def test_format_time(timedelta_obj, expected):
    timing_utils = TimingUtils()
    assert timing_utils.format_time(timedelta_obj) == expected


@pytest.mark.parametrize(
    "input_tracks,expected_tracks",
    [
        # Basic case - no changes needed
        (
            [
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:00:00",
                    end_time="00:01:00",
                ),
                DomainTrack(
                    name="Track 2",
                    artist="Artist 2",
                    start_time="00:01:00",
                    end_time="00:02:00",
                ),
            ],
            [
                ("00:00:00", "00:01:00", "Track 1", "Artist 1"),
                ("00:01:00", "00:02:00", "Track 2", "Artist 2"),
            ],
        ),
        # Duplicate tracks should be merged
        (
            [
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:00:00",
                    end_time="00:01:00",
                ),
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:01:00",
                    end_time="00:02:00",
                ),
            ],
            [
                ("00:00:00", "00:02:00", "Track 1", "Artist 1"),
            ],
        ),
    ],
)
def test_apply_timing_rules(input_tracks, expected_tracks):
    timing_utils = TimingUtils()
    result = timing_utils.apply_timing_rules(input_tracks)

    assert len(result) == len(expected_tracks)
    for i, (expected_start, expected_end, expected_name, expected_artist) in enumerate(
        expected_tracks
    ):
        assert result[i].start_time == expected_start
        assert result[i].end_time == expected_end
        assert result[i].name == expected_name
        assert result[i].artist == expected_artist


@pytest.mark.parametrize(
    "input_tracks,expected_tracks",
    [
        # Duplicate tracks should be merged
        (
            [
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:00:00",
                    end_time="00:01:00",
                ),
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:01:00",
                    end_time="00:02:00",
                ),
            ],
            [
                ("00:00:00", "00:02:00", "Track 1", "Artist 1"),
            ],
        ),
    ],
)
def test_deduplicate_tracks(input_tracks, expected_tracks):
    timing_utils = TimingUtils()
    result = timing_utils.apply_timing_rules(input_tracks)

    assert len(result) == len(expected_tracks)
    for i, (expected_start, expected_end, expected_name, expected_artist) in enumerate(
        expected_tracks
    ):
        assert result[i].start_time == expected_start
        assert result[i].end_time == expected_end
        assert result[i].name == expected_name
        assert result[i].artist == expected_artist


@pytest.mark.parametrize(
    "input_tracks,expected_tracks",
    [
        # Track starting at 00:00:30 should get intro track
        (
            [
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:00:30",
                    end_time="00:01:00",
                ),
            ],
            [
                ("00:00:00", "00:00:30", "ID", "ID"),
                ("00:00:30", "00:01:00", "Track 1", "Artist 1"),
            ],
        ),
        # Track starting at 00:00:00 should not get intro track
        (
            [
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:00:00",
                    end_time="00:01:00",
                ),
            ],
            [
                ("00:00:00", "00:01:00", "Track 1", "Artist 1"),
            ],
        ),
    ],
)
def test_add_intro_track(input_tracks, expected_tracks):
    timing_utils = TimingUtils()
    result = timing_utils.apply_timing_rules(input_tracks)

    assert len(result) == len(expected_tracks)
    for i, (expected_start, expected_end, expected_name, expected_artist) in enumerate(
        expected_tracks
    ):
        assert result[i].start_time == expected_start
        assert result[i].end_time == expected_end
        assert result[i].name == expected_name
        assert result[i].artist == expected_artist


@pytest.mark.parametrize(
    "input_tracks,expected_tracks",
    [
        # Gap longer than 60 seconds should get ID track
        (
            [
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:00:00",
                    end_time="00:01:00",
                ),
                DomainTrack(
                    name="Track 2",
                    artist="Artist 2",
                    start_time="00:02:30",
                    end_time="00:03:30",
                ),
            ],
            [
                ("00:00:00", "00:01:00", "Track 1", "Artist 1"),
                ("00:01:00", "00:02:30", "ID", "ID"),
                ("00:02:30", "00:03:30", "Track 2", "Artist 2"),
            ],
        ),
        # Gap exactly 60 seconds should be adjusted to midpoint
        (
            [
                DomainTrack(
                    name="Track 1",
                    artist="Artist 1",
                    start_time="00:00:00",
                    end_time="00:01:00",
                ),
                DomainTrack(
                    name="Track 2",
                    artist="Artist 2",
                    start_time="00:02:00",
                    end_time="00:03:00",
                ),
            ],
            [
                ("00:00:00", "00:01:30", "Track 1", "Artist 1"),
                ("00:01:30", "00:03:00", "Track 2", "Artist 2"),
            ],
        ),
    ],
)
def test_process_gaps(input_tracks, expected_tracks):
    timing_utils = TimingUtils()
    result = timing_utils.apply_timing_rules(input_tracks)

    assert len(result) == len(expected_tracks)
    for i, (expected_start, expected_end, expected_name, expected_artist) in enumerate(
        expected_tracks
    ):
        assert result[i].start_time == expected_start
        assert result[i].end_time == expected_end
        assert result[i].name == expected_name
        assert result[i].artist == expected_artist
