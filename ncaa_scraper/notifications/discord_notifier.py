"""Discord notification system for the NCAA scraper."""

import requests
import datetime
import logging
from typing import Optional, Dict, Any

from .base_notifier import BaseNotifier
from ..config.constants import ErrorType

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseNotifier):
    """Discord webhook notification system."""
    
    def __init__(self, webhook_url: Optional[str] = None, enabled: bool = True):
        super().__init__(enabled)
        self.webhook_url = webhook_url
        self.enabled = enabled and webhook_url is not None
    
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
        Send a notification to Discord webhook.
        
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
        if not self.enabled or not self.webhook_url:
            logger.debug("Discord webhook not configured or disabled, skipping notification")
            return False
        
        try:
            # Choose emoji based on error type
            emoji_map = {
                ErrorType.ERROR: "🚨",
                ErrorType.WARNING: "⚠️",
                ErrorType.INFO: "ℹ️",
                ErrorType.SUCCESS: "✅",
                ErrorType.GAME_ERROR: "🏀"
            }
            emoji = emoji_map.get(error_type, "📢")
            
            # Build title with context
            title = f"{emoji} NCAA Scraper {error_type.value}"
            if division and gender:
                title += f" - {gender.title()} {division.upper()}"
            
            # Build description with context
            description = message
            fields = []
            
            if date:
                fields.append({
                    "name": "📅 Date",
                    "value": date,
                    "inline": True
                })
            
            if division:
                fields.append({
                    "name": "🏆 Division",
                    "value": division.upper(),
                    "inline": True
                })
            
            if gender:
                fields.append({
                    "name": "⚽ Gender",
                    "value": gender.title(),
                    "inline": True
                })
            
            if game_link:
                fields.append({
                    "name": "🔗 Game Link",
                    "value": f"[View Game]({game_link})",
                    "inline": False
                })
            
            # Create Discord embed
            embed = {
                "title": title,
                "description": description,
                "color": self._get_color_for_error_type(error_type),
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "footer": {
                    "text": "NCAA Basketball Scraper"
                }
            }
            
            if fields:
                embed["fields"] = fields
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.debug(f"Discord notification sent successfully: {error_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
    
    def _get_color_for_error_type(self, error_type: ErrorType) -> int:
        """Get Discord embed color based on error type."""
        color_map = {
            ErrorType.ERROR: 0xff0000,      # Red
            ErrorType.WARNING: 0xffaa00,    # Orange
            ErrorType.INFO: 0x0099ff,       # Blue
            ErrorType.SUCCESS: 0x00ff00,    # Green
            ErrorType.GAME_ERROR: 0xff6600  # Dark orange
        }
        return color_map.get(error_type, 0x666666)  # Default gray
