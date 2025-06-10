from datetime import datetime

from pydantic import BaseModel, Field


class Track(BaseModel):
    """A track in a DJ set"""

    name: str = Field(..., description="The name of the track")
    artist: str = Field(..., description="The artist of the track")
    start_time: datetime = Field(..., description="The start time of the track")
    end_time: datetime = Field(..., description="The end time of the track")


class Tracklist(BaseModel):
    """A tracklist for a DJ set"""

    name: str = Field(..., description="The name of the DJ set")
    year: int = Field(..., description="The year of the DJ set")
    artist: str = Field(..., description="The artist of the DJ set")
    genre: str = Field(..., description="The genre of the DJ set")
    tracks: list[Track] = Field(..., description="The tracks in the DJ set")
