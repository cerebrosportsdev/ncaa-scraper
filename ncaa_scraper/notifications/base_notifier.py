"""Base notification interface for the NCAA scraper."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

from ..config.constants import ErrorType

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """Base class for notification systems."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    @abstractmethod
    def send_notification(
        self,
        message: str,
        error_type: ErrorType,
        division: Optional[str] = None,
        date: Optional[str] = None,
        gender: Optional[str] = None,
        game_link: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Send a notification.
        
        Args:
            message: Message to send
            error_type: Type of notification
            division: Division (d1, d2, d3)
            date: Date in YYYY-MM-DD format
            gender: Gender (men, women)
            game_link: Specific game link if applicable
            **kwargs: Additional parameters
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if notifier is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable the notifier."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the notifier."""
        self.enabled = False
