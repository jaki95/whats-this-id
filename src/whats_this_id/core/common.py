"""
Common utilities and base classes for the core module.
"""
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from pydantic import BaseModel, Field
from dj_set_downloader.models.domain_tracklist import DomainTracklist
from dj_set_downloader.models.domain_track import DomainTrack

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Standard result container for all operations."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseOperation(ABC):
    """Base class for all operations with common error handling and timing."""
    
    def __init__(self, name: str, timeout: int = 30, max_retries: int = 3):
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = 1

    async def execute_async(self, *args, **kwargs) -> ExecutionResult:
        """Execute the operation asynchronously with error handling and timing."""
        start_time = datetime.now()
        
        for attempt in range(self.max_retries):
            try:
                result = await asyncio.wait_for(
                    self._execute_async(*args, **kwargs),
                    timeout=self.timeout
                )
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                return ExecutionResult(
                    success=True,
                    data=result,
                    duration_ms=duration,
                    metadata={"attempt": attempt + 1}
                )
                
            except asyncio.TimeoutError:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                error_msg = f"Operation '{self.name}' timed out after {self.timeout}s"
                logger.warning(f"{error_msg} (attempt {attempt + 1}/{self.max_retries})")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
                return ExecutionResult(
                    success=False,
                    error=error_msg,
                    duration_ms=duration,
                    metadata={"attempt": attempt + 1}
                )
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                error_msg = f"Operation '{self.name}' failed: {str(e)}"
                logger.error(f"{error_msg} (attempt {attempt + 1}/{self.max_retries})")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
                return ExecutionResult(
                    success=False,
                    error=error_msg,
                    duration_ms=duration,
                    metadata={"attempt": attempt + 1}
                )
        
        # This should never be reached, but just in case
        duration = (datetime.now() - start_time).total_seconds() * 1000
        return ExecutionResult(
            success=False,
            error=f"Operation '{self.name}' failed after {self.max_retries} attempts",
            duration_ms=duration,
            metadata={"attempt": self.max_retries}
        )

    def execute(self, *args, **kwargs) -> ExecutionResult:
        """Execute the operation synchronously."""
        return asyncio.run(self.execute_async(*args, **kwargs))

    @abstractmethod
    async def _execute_async(self, *args, **kwargs) -> Any:
        """Implement the actual operation logic."""
        pass


class StepLog(BaseModel):
    """A step log for a search run."""
    step_name: str
    source: str
    status: str
    details: str = ""
    confidence: Optional[float] = None
    found_tracks: Optional[int] = None
    link: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class SearchRun(BaseModel):
    """A search run."""
    query: str
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    steps: List[StepLog] = Field(default_factory=list)
    final_tracklist: DomainTracklist = Field(default_factory=DomainTracklist)
    total_duration_ms: Optional[float] = None
    success: bool = False


def log_step(run: SearchRun, step_name: str, source: str, status: str, 
             details: str = "", found_tracks: Optional[int] = None, 
             confidence: Optional[float] = None, link: Optional[str] = None,
             error: Optional[str] = None, duration_ms: Optional[float] = None) -> None:
    """Helper function to log a step."""
    run.steps.append(
        StepLog(
            step_name=step_name,
            source=source,
            status=status,
            details=details,
            found_tracks=found_tracks,
            confidence=confidence,
            link=link,
            error=error,
            duration_ms=duration_ms
        )
    )
