import json
import time
import requests
from typing import Optional, Any
from pathlib import Path

from whats_this_id.core.downloader.jobs import JobStatus
from whats_this_id.core.models.tracklist import Tracklist





class DJSetProcessorClient:
    """
    Enhanced client for interacting with the DJ Set Processor service
    with download capabilities and improved job status handling.
    """

    # def __init__(self, base_url: str = "http://192.168.1.173:8000"):
    def __init__(self, base_url: str = "http://localhost:8000"):

        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def health_check(self) -> dict:
        """Check if the service is healthy."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def process_set(
        self,
        download_url: str,
        tracklist: Tracklist,
        file_extension: str = "m4a",
        max_concurrent_tasks: int = 4,
    ) -> str:
        """
        Process a DJ set using Pydantic models.

        Args:
            download_url: URL to download the audio file from
            tracklist: Pydantic Tracklist model instance
            file_extension: Output file extension (mp3, m4a, wav, flac)
            max_concurrent_tasks: Number of concurrent tasks

        Returns:
            Job ID for tracking
        """
        tracklist_data = tracklist.model_dump()

        payload = {
            "url": download_url,
            "tracklist": json.dumps(tracklist_data),
            "file_extension": file_extension,
            "max_concurrent_tasks": max_concurrent_tasks,
        }

        response = self.session.post(f"{self.base_url}/api/process", json=payload)
        response.raise_for_status()

        result = response.json()
        return result["jobId"]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        response = self.session.post(f"{self.base_url}/api/jobs/{job_id}/cancel")
        return response.status_code == 200

    def get_job_status(self, job_id: str) -> JobStatus:
        """Get the enhanced status of a specific job."""
        try:
            response = self.session.get(f"{self.base_url}/api/jobs/{job_id}")
            response.raise_for_status()
            
            data = response.json()
            
            # Add debugging information for troubleshooting
            print(f"API Response for job {job_id}: {data}")
            
            # Validate critical fields before model validation
            if 'events' in data and data['events'] is None:
                print(f"Warning: API returned null events for job {job_id}, will be converted to empty list")
            
            if 'tracks' in data and data['tracks'] is None:
                print(f"Warning: API returned null tracks for job {job_id}, will be converted to empty list")
            
            return JobStatus.model_validate(data)
            
        except Exception as e:
            print(f"Error getting job status for {job_id}: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"API Response text: {e.response.text}")
            raise

    def get_tracks_info(self, job_id: str) -> dict[str, Any]:
        """Get detailed track information for a completed job."""
        response = self.session.get(f"{self.base_url}/api/jobs/{job_id}/tracks")
        response.raise_for_status()
        return response.json()

    def download_all_tracks(self, job_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Download all tracks as a ZIP file.
        
        Args:
            job_id: Job ID to download tracks from
            output_path: Optional path to save the ZIP file
            
        Returns:
            Path to the downloaded ZIP file
        """
        response = self.session.get(
            f"{self.base_url}/api/jobs/{job_id}/download", 
            stream=True
        )
        response.raise_for_status()
        
        # Extract filename from Content-Disposition header
        filename = "tracks.zip"
        if "Content-Disposition" in response.headers:
            import re
            cd = response.headers["Content-Disposition"]
            filename_match = re.findall(r'filename="(.+)"', cd)
            if filename_match:
                filename = filename_match[0]
        
        if output_path is None:
            output_path = Path(filename)
        elif output_path.is_dir():
            output_path = output_path / filename
            
        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rDownloading: {progress:.1f}%", end="", flush=True)
        
        print(f"\n✅ Downloaded: {output_path}")
        return output_path

    def download_track(
        self, 
        job_id: str, 
        track_number: int, 
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Download a single track.
        
        Args:
            job_id: Job ID to download track from
            track_number: Track number (1-indexed)
            output_path: Optional path to save the track file
            
        Returns:
            Path to the downloaded track file
        """
        response = self.session.get(
            f"{self.base_url}/api/jobs/{job_id}/tracks/{track_number}/download",
            stream=True
        )
        response.raise_for_status()
        
        # Extract filename from Content-Disposition header
        filename = f"track_{track_number}.mp3"
        if "Content-Disposition" in response.headers:
            import re
            cd = response.headers["Content-Disposition"]
            filename_match = re.findall(r'filename="(.+)"', cd)
            if filename_match:
                filename = filename_match[0]
        
        if output_path is None:
            output_path = Path(filename)
        elif output_path.is_dir():
            output_path = output_path / filename
            
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"✅ Downloaded track {track_number}: {output_path}")
        return output_path

    def list_jobs(self, page: int = 1, page_size: int = 10) -> dict:
        """List all jobs with pagination."""
        params = {"page": page, "pageSize": page_size}
        response = self.session.get(f"{self.base_url}/api/jobs", params=params)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self, 
        job_id: str, 
        poll_interval: float = 2.0, 
        timeout: float = 3600.0
    ) -> JobStatus:
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

            print(
                f"Job {job_id}: {status.status} - {status.progress:.1f}% - {status.message}"
            )

            if status.status in ["completed", "failed", "cancelled"]:
                return status

            time.sleep(poll_interval)

        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


def process_dj_set(
    dj_set_url: str, 
    tracklist, 
    download_dir: Optional[Path] = None,
    download_individual: bool = False
) -> None:
    """
    Enhanced DJ set processing with download capabilities.
    
    Args:
        dj_set_url: URL to the DJ set
        tracklist: Pydantic Tracklist model
        download_dir: Directory to save downloaded files (default: current dir)
        download_individual: Whether to download individual tracks as well
    """
    processor = DJSetProcessorClient()
    
    if download_dir is None:
        download_dir = Path.cwd()
    download_dir.mkdir(exist_ok=True)

    try:
        # Check health
        health = processor.health_check()
        print(f"Service health: {health['status']}")

        # Validate the tracklist
        print(f"Created tracklist: {tracklist.artist} - {tracklist.name}")
        print(f"Tracks: {len(tracklist.tracks)}")
        for i, track in enumerate(tracklist.tracks, 1):
            print(
                f"  {i}. {track.artist} - {track.name} ({track.start_time} - {track.end_time})"
            )

        # Process the set
        print("\nSubmitting processing job...")
        job_id = processor.process_set(
            download_url=dj_set_url,
            tracklist=tracklist,
            file_extension="m4a",
            max_concurrent_tasks=4,
        )

        print(f"Job ID: {job_id}")

        # Wait for completion
        final_status = processor.wait_for_completion(job_id)

        if final_status.status == "completed":
            print("\n✅ Processing completed!")
            
            # Display track information
            if final_status.tracks:
                print(f"\n📁 Available tracks ({final_status.total_tracks}):")
                for track in final_status.tracks:
                    size_mb = track.size_bytes / (1024 * 1024)
                    status_icon = "✅" if track.available else "❌"
                    print(f"  {status_icon} {track.track_number}. {track.artist} - {track.name} ({size_mb:.1f} MB)")
            
            # Download all tracks as ZIP
            print(f"\n📦 Downloading all tracks as ZIP...")
            zip_path = processor.download_all_tracks(job_id, download_dir)
            
            # Optionally download individual tracks
            if download_individual and final_status.tracks:
                print(f"\n🎵 Downloading individual tracks...")
                track_dir = download_dir / f"{tracklist.artist} - {tracklist.name}"
                track_dir.mkdir(exist_ok=True)
                
                for track in final_status.tracks:
                    if track.available:
                        processor.download_track(job_id, track.track_number, track_dir)
            
            print(f"\n🎉 All downloads complete!")
            print(f"📂 Files saved to: {download_dir}")
            
        else:
            print(f"\n❌ Processing failed: {final_status.error}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
