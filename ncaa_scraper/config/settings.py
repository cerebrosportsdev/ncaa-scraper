"""Configuration management for the NCAA scraper."""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

from .constants import DEFAULT_OUTPUT_DIR, DEFAULT_TOKEN_FILE, DEFAULT_REDIRECT_URI


@dataclass
class ScraperConfig:
    """Configuration for the NCAA scraper."""
    
    # Google Drive credentials
    google_client_id: Optional[str]
    google_client_secret: Optional[str]
    google_redirect_uri: str
    google_drive_folder_id: Optional[str]
    token_file: str
    
    # Discord notifications
    discord_webhook_url: Optional[str]
    
    # Scraping configuration
    output_dir: str
    wait_timeout: int = 15
    sleep_time: int = 2
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> 'ScraperConfig':
        """Create configuration from environment variables."""
        load_dotenv()
        
        return cls(
            google_client_id=os.getenv('GOOGLE_CLIENT_ID'),
            google_client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            google_redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', DEFAULT_REDIRECT_URI),
            google_drive_folder_id=os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
            discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL'),
            token_file=os.getenv('GOOGLE_TOKEN_FILE', DEFAULT_TOKEN_FILE),
            output_dir=os.getenv('OUTPUT_DIR', DEFAULT_OUTPUT_DIR),
            wait_timeout=int(os.getenv('WAIT_TIMEOUT', '15')),
            sleep_time=int(os.getenv('SLEEP_TIME', '2')),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
    
    def validate(self) -> bool:
        """Validate the configuration."""
        # Google Drive credentials are optional - only validate if upload is enabled
        return True


def get_config() -> ScraperConfig:
    """Get the scraper configuration."""
    config = ScraperConfig.from_env()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    return config
