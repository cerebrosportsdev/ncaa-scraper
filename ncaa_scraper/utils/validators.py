"""Validation utility functions for the NCAA scraper."""

import os
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def validate_date_string(date_str: str) -> bool:
    """Validate date string format (YYYY/MM/DD)."""
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y/%m/%d')
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def validate_file_path(file_path: str) -> bool:
    """Validate if file path is accessible."""
    try:
        return os.path.exists(file_path) and os.path.isfile(file_path)
    except Exception:
        return False


def validate_directory_path(dir_path: str) -> bool:
    """Validate if directory path is accessible."""
    try:
        return os.path.exists(dir_path) and os.path.isdir(dir_path)
    except Exception:
        return False


def validate_required_fields(data: dict, required_fields: list) -> bool:
    """Validate that all required fields are present in data."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
        return False
    return True


def validate_positive_integer(value: Any, field_name: str) -> bool:
    """Validate that value is a positive integer."""
    try:
        int_value = int(value)
        if int_value <= 0:
            logger.error(f"{field_name} must be a positive integer, got: {value}")
            return False
        return True
    except (ValueError, TypeError):
        logger.error(f"{field_name} must be a valid integer, got: {value}")
        return False
