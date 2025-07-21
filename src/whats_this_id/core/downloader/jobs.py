from pydantic import BaseModel, Field
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
    events: list[dict[str, Any]] = []
    results: Optional[list[str]] = None
    start_time: str
    end_time: Optional[str] =None
    error: Optional[str] = None
    tracklist: Optional[dict[str, Any]] = None
    tracks: list[TrackInfo] = []
    download_all_url: Optional[str] = None
    total_tracks: Optional[int] = None
    
    class Config:
        populate_by_name = True