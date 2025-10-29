"""Configuration management for NCAA scraper."""

from .settings import ScraperConfig, get_config
from .constants import ErrorType, Division, Gender

__all__ = ['ScraperConfig', 'get_config', 'ErrorType', 'Division', 'Gender']
