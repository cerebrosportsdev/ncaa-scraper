"""Selenium utility functions for the NCAA scraper."""

import time
import logging
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)


class SeleniumUtils:
    """Utility class for Selenium operations."""
    
    @staticmethod
    def create_driver(headless: bool = False) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver.
        
        Args:
            headless: Whether to run in headless mode
        
        Returns:
            Configured Chrome WebDriver
        """
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        return webdriver.Chrome(options=options)
    
    @staticmethod
    def wait_for_element(driver: webdriver.Chrome, by: By, value: str, timeout: int = 15) -> Optional[object]:
        """
        Wait for an element to be present on the page.
        
        Args:
            driver: WebDriver instance
            by: Selenium By selector
            value: Selector value
            timeout: Maximum time to wait in seconds
        
        Returns:
            WebElement if found, None otherwise
        """
        try:
            wait = WebDriverWait(driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            logger.warning(f"Element not found: {by}={value}")
            return None
    
    @staticmethod
    def wait_for_elements(driver: webdriver.Chrome, by: By, value: str, timeout: int = 15) -> List[object]:
        """
        Wait for elements to be present on the page.
        
        Args:
            driver: WebDriver instance
            by: Selenium By selector
            value: Selector value
            timeout: Maximum time to wait in seconds
        
        Returns:
            List of WebElements found
        """
        try:
            wait = WebDriverWait(driver, timeout)
            elements = wait.until(EC.presence_of_all_elements_located((by, value)))
            return elements
        except TimeoutException:
            logger.warning(f"Elements not found: {by}={value}")
            return []
    
    @staticmethod
    def safe_click(element) -> bool:
        """
        Safely click an element.
        
        Args:
            element: WebElement to click
        
        Returns:
            True if click successful, False otherwise
        """
        try:
            element.click()
            return True
        except WebDriverException as e:
            logger.warning(f"Failed to click element: {e}")
            return False
    
    @staticmethod
    def safe_get_text(element) -> str:
        """
        Safely get text from an element.
        
        Args:
            element: WebElement to get text from
        
        Returns:
            Element text or empty string if failed
        """
        try:
            return element.text.strip()
        except WebDriverException as e:
            logger.warning(f"Failed to get text from element: {e}")
            return ""
    
    @staticmethod
    def safe_get_attribute(element, attribute: str) -> str:
        """
        Safely get attribute from an element.
        
        Args:
            element: WebElement to get attribute from
            attribute: Attribute name
        
        Returns:
            Attribute value or empty string if failed
        """
        try:
            return element.get_attribute(attribute) or ""
        except WebDriverException as e:
            logger.warning(f"Failed to get attribute {attribute} from element: {e}")
            return ""
    
    @staticmethod
    def check_page_loaded(driver: webdriver.Chrome, expected_elements: List[str], timeout: int = 15) -> bool:
        """
        Check if page loaded successfully by looking for expected elements.
        
        Args:
            driver: WebDriver instance
            expected_elements: List of CSS selectors to look for
            timeout: Maximum time to wait in seconds
        
        Returns:
            True if page loaded successfully, False otherwise
        """
        for selector in expected_elements:
            try:
                wait = WebDriverWait(driver, timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                return True
            except TimeoutException:
                continue
        
        return False
    
    @staticmethod
    def check_for_errors(driver: webdriver.Chrome) -> Optional[str]:
        """
        Check for common error pages.
        
        Args:
            driver: WebDriver instance
        
        Returns:
            Error message if error found, None otherwise
        """
        try:
            # Check for 404 error
            if "404" in driver.title or "not found" in driver.title.lower():
                return "Page not found (404)"
            
            # Check for error page
            if "error" in driver.title.lower():
                return "Error page detected"
            
            # Check for specific NCAA 404 error
            error_404 = driver.find_elements(By.CLASS_NAME, "error-404")
            if error_404:
                return "NCAA 404 error - 'That's a foul on us...'"
            
            # Check for unavailable content
            if "unavailable" in driver.page_source.lower():
                return "Content unavailable"
            
            return None
            
        except Exception as e:
            logger.warning(f"Error checking for page errors: {e}")
            return None
