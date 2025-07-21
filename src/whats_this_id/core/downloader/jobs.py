from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any


class TrackInfo(BaseModel):
    track_number: int
    name: str
    artist: str
    start_time: str
    end_time: str
    download_url: str
    size_bytes: int
    available: bool


class JobStatus(BaseModel):
    id: str
    status: str
    progress: float
    message: str
    events: Optional[list[dict[str, Any]]] = []
    results: Optional[list[str]] = None
    start_time: str
    end_time: Optional[str] = None
    error: Optional[str] = None
    tracklist: Optional[dict[str, Any]] = None
    tracks: Optional[list[TrackInfo]] = []
    download_all_url: Optional[str] = None
    total_tracks: Optional[int] = None
    
    @field_validator('events', mode='before')
    @classmethod
    def validate_events(cls, v):
        """Convert None to empty list for events."""
        if v is None:
            return []
        return v
    
    @field_validator('tracks', mode='before')
    @classmethod
    def validate_tracks(cls, v):
        """Convert None to empty list for tracks."""
        if v is None:
            return []
        return v
    
    @field_validator('results', mode='before')
    @classmethod
    def validate_results(cls, v):
        """Convert None to empty list for results if needed."""
        if v is None:
            return None  # Keep as None since this field is Optional
        return v
    
    class Config:
        populate_by_name = True