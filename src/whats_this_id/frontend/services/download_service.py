"""Download service for DJ set tracks."""

import streamlit as st
import tempfile
import re
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from whats_this_id.frontend.config import AppConfig


class DownloadService:
    """Service for handling track downloads."""
    
    _instance: Optional['DownloadService'] = None
    _initialized: bool = False
    
    def __new__(cls, base_url: str = AppConfig.DEFAULT_API_BASE_URL):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, base_url: str = AppConfig.DEFAULT_API_BASE_URL):
        """Initialize the download service (only once)."""
        if not self._initialized:
            self.base_url = base_url.rstrip("/")
            import requests
            self.session = requests.Session()
            self._initialized = True
    
    def download_all_tracks(self, job_id: str) -> Optional[Tuple[bytes, str]]:
        """Download all tracks as ZIP with proper error handling.
        
        Args:
            job_id: The processing job ID
            
        Returns:
            Tuple of (file_data, filename) if successful, None if failed
        """
        try:
            # Make direct HTTP request to get the file data
            response = self.session.get(
                f"{self.base_url}/api/jobs/{job_id}/download", 
                stream=True
            )
            response.raise_for_status()
            
            # Get file data directly from response
            file_data = response.content
            
            # Extract filename from Content-Disposition header
            filename = "tracks.zip"
            if "Content-Disposition" in response.headers:
                cd = response.headers["Content-Disposition"]
                filename_match = re.findall(r'filename="(.+)"', cd)
                if filename_match:
                    filename = filename_match[0]
            
            # Verify it's a valid ZIP file (starts with PK)
            if file_data and len(file_data) >= 4:
                if file_data[:4] == b'PK\x03\x04' or file_data[:4] == b'PK\x05\x06':
                    return file_data, filename
                else:
                    st.error("Downloaded file is not a valid ZIP file")
                    return None
            else:
                st.error("Downloaded file is empty or invalid")
                return None
                
        except Exception as e:
            st.error(f"Error downloading tracks: {e}")
            return None
    
    def download_single_track(self, job_id: str, track_name: str) -> Optional[Tuple[bytes, str]]:
        """Download a single track file.
        
        Args:
            job_id: The processing job ID
            track_name: Name of the track to download
            
        Returns:
            Tuple of (file_data, filename) if successful, None if failed
        """
        try:
            # URL encode the track name for the API request
            import urllib.parse
            encoded_track = urllib.parse.quote(track_name)
            
            response = self.session.get(
                f"{self.base_url}/api/jobs/{job_id}/download/{encoded_track}"
            )
            response.raise_for_status()
            
            file_data = response.content
            
            # Get filename from headers or use track name
            filename = track_name
            if "Content-Disposition" in response.headers:
                cd = response.headers["Content-Disposition"]
                filename_match = re.findall(r'filename="(.+)"', cd)
                if filename_match:
                    filename = filename_match[0]
            
            return file_data, filename
            
        except Exception as e:
            st.error(f"Error downloading track '{track_name}': {e}")
            return None
    
    def get_tracks_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed track information for a completed job.
        
        Args:
            job_id: The processing job ID
            
        Returns:
            Dictionary with track information if successful, None if failed
        """
        try:
            response = self.session.get(f"{self.base_url}/api/jobs/{job_id}/tracks")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error getting tracks info: {e}")
            return None
    
    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Get MIME type for a file based on its extension."""
        extension = Path(filename).suffix.lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
            '.zip': 'application/zip'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"


def get_download_service() -> DownloadService:
    """Get the singleton download service instance."""
    return DownloadService() 