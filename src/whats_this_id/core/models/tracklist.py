import re

from pydantic import BaseModel, Field, field_validator


class Track(BaseModel):
    """A track in a DJ set"""

    name: str = Field(..., description="The name of the track")
    artist: str = Field(..., description="The artist of the track")
    start_time: str = Field(
        ..., description="The start time of the track (HH:MM:SS in 24-hour format)"
    )
    end_time: str = Field(
        ..., description="The end time of the track (HH:MM:SS in 24-hour format)"
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time is in HH:MM:SS format and convert to 24-hour format if needed"""
        # Check if time matches HH:MM:SS pattern
        if not re.match(r"^\d{1,2}:\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM:SS format")

        # Split into hours, minutes, seconds
        hours, minutes, seconds = map(int, v.split(":"))

        # Convert hours > 24 to 24-hour format
        if hours >= 24:
            hours = hours % 24

        # Validate minutes and seconds
        if minutes >= 60 or seconds >= 60:
            raise ValueError("Minutes and seconds must be less than 60")

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class Tracklist(BaseModel):
    """A tracklist for a DJ set"""

    name: str = Field(..., description="The name of the DJ set")
    year: int = Field(..., description="The year of the DJ set")
    artist: str = Field(..., description="The artist of the DJ set")
    genre: str = Field(..., description="The genre of the DJ set")
    tracks: list[Track] = Field(..., description="The tracks in the DJ set")
