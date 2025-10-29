"""URL utility functions for the NCAA scraper."""

from typing import List, Dict, Any
from urllib.parse import urlparse
import logging

from ..config.constants import NCAA_BASE_URL, Division, Gender

logger = logging.getLogger(__name__)


def generate_ncaa_urls(
    date_str: str,
    divisions: List[Division] = None,
    genders: List[Gender] = None
) -> List[str]:
    """
    Generate NCAA scoreboard URLs for given date and parameters.
    
    Args:
        date_str: Date in YYYY/MM/DD format
        divisions: List of divisions to scrape
        genders: List of genders to scrape
    
    Returns:
        List of NCAA scoreboard URLs
    """
    if divisions is None:
        divisions = [Division.D3]
    if genders is None:
        genders = [Gender.WOMEN]
    
    urls = []
    for gender in genders:
        for division in divisions:
            url = NCAA_BASE_URL.format(
                gender=gender.value,
                division=division.value,
                date=date_str
            )
            urls.append(url)
    
    return urls


def parse_url_components(url: str) -> Dict[str, str]:
    """
    Parse NCAA URL to extract components.
    
    Args:
        url: NCAA scoreboard URL
    
    Returns:
        Dictionary with parsed components (gender, division, year, month, day)
    """
    try:
        # URL format: .../basketball-women/d3/2025/02/06/all-conf
        parts = url.split('/')
        
        # Find the basketball part
        basketball_index = -1
        for i, part in enumerate(parts):
            if part.startswith('basketball-'):
                basketball_index = i
                break
        
        if basketball_index == -1:
            raise ValueError("Invalid NCAA URL format")
        
        gender = parts[basketball_index].split('-')[1]  # women or men
        division = parts[basketball_index + 1]  # d1, d2, d3
        year = parts[basketball_index + 2]  # 2025
        month = parts[basketball_index + 3]  # 01, 02, etc.
        day = parts[basketball_index + 4]  # 15, 21, etc.
        
        return {
            'gender': gender,
            'division': division,
            'year': year,
            'month': month,
            'day': day
        }
    except (IndexError, ValueError) as e:
        logger.error(f"Failed to parse URL components from {url}: {e}")
        raise ValueError(f"Invalid URL format: {url}")


def validate_url(url: str) -> bool:
    """Validate if URL is a valid NCAA scoreboard URL."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Check if it's an NCAA URL
        if 'ncaa.com' not in parsed.netloc:
            return False
        
        # Check if it's a scoreboard URL
        if '/scoreboard/' not in parsed.path:
            return False
        
        return True
    except Exception:
        return False


def extract_game_id_from_url(url: str) -> str:
    """Extract game ID from game URL."""
    return url.split('/')[-1]
