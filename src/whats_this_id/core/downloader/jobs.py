from dataclasses import dataclass
from typing import Optional


@dataclass
class JobStatus:
    id: str
    status: str
    progress: float
    message: str
    start_time: str
    end_time: Optional[str] = None
    error: Optional[str] = None
    results: Optional[list[str]] = None
