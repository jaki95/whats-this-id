from whats_this_id.core.models.tracklist import Tracklist
from .jobs import JobStatus

import requests
import json
import time


class DJSetProcessorClient:
    """
    Client for interacting with the DJ Set Processor service 
    using Pydantic models and tracklist data.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """Check if the service is healthy."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def process_set(self, download_url: str, tracklist: Tracklist, 
                   file_extension: str = "m4a", max_concurrent_tasks: int = 4) -> str:
        """
        Process a DJ set using Pydantic models.
        
        Args:
            download_url: URL to download the audio file from
            tracklist: Pydantic Tracklist model instance
            file_extension: Output file extension
            max_concurrent_tasks: Number of concurrent tasks
        
        Returns:
            Job ID for tracking
        """
        tracklist_data = tracklist.model_dump()
        
        payload = {
            "url": download_url,
            "tracklist": json.dumps(tracklist_data),
            "fileExtension": file_extension,
            "maxConcurrentTasks": max_concurrent_tasks
        }
        
        response = self.session.post(
            f"{self.base_url}/api/process",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        return result["jobId"]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        response = self.session.post(f"{self.base_url}/api/jobs/{job_id}/cancel")
        return response.status_code == 200
    
    def get_job_status(self, job_id: str) -> JobStatus:
        """Get the status of a specific job."""
        response = self.session.get(f"{self.base_url}/api/jobs/{job_id}")
        response.raise_for_status()
        
        data = response.json()
        return JobStatus(
            id=data["id"],
            status=data["status"],
            progress=data["progress"],
            message=data["message"],
            start_time=data["startTime"],
            end_time=data.get("endTime"),
            error=data.get("error"),
            results=data.get("results")
        )
    
    def list_jobs(self, page: int = 1, page_size: int = 10) -> dict:
        """List all jobs with pagination."""
        params = {"page": page, "pageSize": page_size}
        response = self.session.get(
            f"{self.base_url}/api/jobs",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id: str, poll_interval: float = 2.0, 
                          timeout: float = 3600.0) -> JobStatus:
        """
        Wait for a job to complete, polling at regular intervals.
        
        Args:
            job_id: Job ID to wait for
            poll_interval: Time between status checks in seconds
            timeout: Maximum time to wait in seconds
            
        Returns:
            Final job status
            
        Raises:
            TimeoutError: If the job doesn't complete within the timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            print(f"Job {job_id}: {status.status} - {status.progress:.1f}% - {status.message}")
            
            if status.status in ["completed", "failed", "cancelled"]:
                return status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


def process_dj_set(dj_set_url: str, tracklist: Tracklist) -> None:
    processor = DJSetProcessorClient()
    
    try:
        # Check health
        health = processor.health_check()
        print(f"Service health: {health['status']}")
        
        # Validate the tracklist
        print(f"Created tracklist: {tracklist.artist} - {tracklist.name}")
        print(f"Tracks: {len(tracklist.tracks)}")
        for i, track in enumerate(tracklist.tracks, 1):
            print(f"  {i}. {track.artist} - {track.name} ({track.start_time} - {track.end_time})")
        
        # Process the set
        print(f"\nSubmitting processing job...")
        job_id = processor.process_set(
            download_url=dj_set_url,
            tracklist=tracklist,
            file_extension="m4a",
            max_concurrent_tasks=4
        )
        
        print(f"Job ID: {job_id}")
        
        # Wait for completion
        final_status = processor.wait_for_completion(job_id)
        
        if final_status.status == "completed":
            print(f"\n✅ Processing completed!")
            print(f"Output files:")
            for file_path in final_status.results:
                print(f"  - {file_path}")
        else:
            print(f"\n❌ Processing failed: {final_status.error}")
            
    except Exception as e:
        print(f"Error: {e}")