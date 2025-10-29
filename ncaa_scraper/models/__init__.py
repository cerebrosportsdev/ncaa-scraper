"""Data models for the NCAA scraper."""

from .game_data import GameData, TeamData
from .scraping_config import ScrapingConfig, DateRange

__all__ = ['GameData', 'TeamData', 'ScrapingConfig', 'DateRange']
