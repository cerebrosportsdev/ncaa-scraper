"""File management utilities for the NCAA scraper."""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for the scraper."""
    
    def __init__(self, base_output_dir: str = "scraped_data"):
        self.base_output_dir = base_output_dir
    
    def create_directory_structure(self, year: str, month: str, gender: str, division: str) -> str:
        """
        Create directory structure: base_output_dir/year/month/gender/division
        
        Args:
            year: Year (e.g., "2025")
            month: Month (e.g., "01")
            gender: Gender (e.g., "men", "women")
            division: Division (e.g., "d1", "d2", "d3")
        
        Returns:
            Path to the created directory
        """
        dir_path = os.path.join(self.base_output_dir, year, month, gender, division)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path
    
    def get_csv_path(self, year: str, month: str, day: str, gender: str, division: str) -> str:
        """
        Get the CSV file path for a specific date and parameters.
        
        Args:
            year: Year (e.g., "2025")
            month: Month (e.g., "01")
            day: Day (e.g., "15")
            gender: Gender (e.g., "men", "women")
            division: Division (e.g., "d1", "d2", "d3")
        
        Returns:
            Full path to the CSV file
        """
        # Create directory structure
        dir_path = self.create_directory_structure(year, month, gender, division)
        
        # Generate filename
        filename = f"basketball_{gender}_{division}_{year}_{month}_{day}.csv"
        return os.path.join(dir_path, filename)
    
    def file_exists_and_has_content(self, file_path: str) -> bool:
        """
        Check if file exists and has content.
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if file exists and has content, False otherwise
        """
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    
    def ensure_directory_exists(self, directory_path: str) -> None:
        """
        Ensure directory exists, create if it doesn't.
        
        Args:
            directory_path: Path to the directory
        """
        os.makedirs(directory_path, exist_ok=True)
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to the file
        
        Returns:
            File size in bytes, 0 if file doesn't exist
        """
        try:
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0
        except OSError as e:
            logger.error(f"Error getting file size for {file_path}: {e}")
            return 0
