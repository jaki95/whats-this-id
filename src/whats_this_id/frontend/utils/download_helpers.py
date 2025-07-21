"""Download utility functions for the frontend."""

import streamlit as st
import tempfile
import os
from pathlib import Path
from typing import Optional

from whats_this_id.core.downloader.client import DJSetProcessorClient


def safe_download_all_tracks(job_id: str) -> Optional[tuple[bytes, str]]:
    """
    Safely download all tracks as ZIP with proper error handling.
    
    Returns:
        Tuple of (file_data, filename) if successful, None if failed
    """
    processor = DJSetProcessorClient()
    
    try:
        # Make direct HTTP request to get the file data
        response = processor.session.get(
            f"{processor.base_url}/api/jobs/{job_id}/download", 
            stream=True
        )
        response.raise_for_status()
        
        st.info(f"🔍 Debug: HTTP response status: {response.status_code}")
        st.info(f"🔍 Debug: Content-Length: {response.headers.get('content-length', 'Unknown')}")
        
        # Get file data directly from response
        file_data = response.content
        
        # Extract filename from Content-Disposition header
        filename = "tracks.zip"
        if "Content-Disposition" in response.headers:
            import re
            cd = response.headers["Content-Disposition"]
            filename_match = re.findall(r'filename="(.+)"', cd)
            if filename_match:
                filename = filename_match[0]
        
        st.info(f"🔍 Debug: Got {len(file_data)} bytes directly from HTTP response")
        st.info(f"🔍 Debug: Filename: {filename}")
        
        # Verify it's a valid ZIP file (starts with PK)
        if file_data and len(file_data) >= 4:
            if file_data[:4] == b'PK\x03\x04' or file_data[:4] == b'PK\x05\x06':
                st.info("🔍 Debug: File appears to be a valid ZIP file")
            else:
                st.warning(f"🔍 Debug: File does not appear to be a valid ZIP file. First 4 bytes: {file_data[:4]}")
        else:
            st.error("🔍 Debug: File data is empty or too small")
        
        return file_data, filename
        
    except Exception as e:
        st.error(f"❌ Error downloading all tracks: {e}")
        st.error(f"🔍 Debug: Exception type: {type(e)}")
        return None


def safe_download_track(job_id: str, track_number: int) -> Optional[tuple[bytes, str]]:
    """
    Safely download individual track with proper error handling.
    
    Returns:
        Tuple of (file_data, filename) if successful, None if failed
    """
    processor = DJSetProcessorClient()
    
    try:
        # Make direct HTTP request to get the file data
        response = processor.session.get(
            f"{processor.base_url}/api/jobs/{job_id}/tracks/{track_number}/download",
            stream=True
        )
        response.raise_for_status()
        
        st.info(f"🔍 Debug: HTTP response status: {response.status_code}")
        st.info(f"🔍 Debug: Content-Length: {response.headers.get('content-length', 'Unknown')}")
        
        # Get file data directly from response
        file_data = response.content
        
        # Extract filename from Content-Disposition header
        filename = f"track_{track_number}.mp3"
        if "Content-Disposition" in response.headers:
            import re
            cd = response.headers["Content-Disposition"]
            filename_match = re.findall(r'filename="(.+)"', cd)
            if filename_match:
                filename = filename_match[0]
        
        st.info(f"🔍 Debug: Got {len(file_data)} bytes directly from HTTP response")
        st.info(f"🔍 Debug: Filename: {filename}")
        
        return file_data, filename
        
    except Exception as e:
        st.error(f"❌ Error downloading track {track_number}: {e}")
        st.error(f"🔍 Debug: Exception type: {type(e)}")
        return None


def get_mime_type(filename: str) -> str:
    """Get appropriate MIME type based on file extension."""
    extension = Path(filename).suffix.lower()
    
    mime_types = {
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.zip': 'application/zip'
    }
    
    return mime_types.get(extension, 'application/octet-stream')


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB" 