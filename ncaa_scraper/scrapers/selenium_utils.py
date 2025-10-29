"""Selenium utility functions for the NCAA scraper."""

import time
import logging
import os
import shutil
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException, SessionNotCreatedException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class SeleniumUtils:
    """Utility class for Selenium operations."""
    
    @staticmethod
    def create_driver(headless: bool = False, max_retries: int = 3) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver with retry logic.
        
        Args:
            headless: Whether to run in headless mode
            max_retries: Maximum number of retry attempts
        
        Returns:
            Configured Chrome WebDriver
            
        Raises:
            SessionNotCreatedException: If unable to create driver after all retries
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Creating Chrome driver (attempt {attempt + 1}/{max_retries})")
                
                # Configure Chrome options
                options = Options()
                
                # Always run headless in Docker or when requested
                if headless or os.getenv('DOCKER_CONTAINER', 'false').lower() == 'true':
                    options.add_argument("--headless=new")
                
                # Essential Chrome options for stability
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-software-rasterizer")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-setuid-sandbox")
                options.add_argument("--disable-background-timer-throttling")
                options.add_argument("--disable-backgrounding-occluded-windows")
                options.add_argument("--disable-renderer-backgrounding")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-plugins")
                options.add_argument("--disable-web-security")
                options.add_argument("--disable-features=VizDisplayCompositor")
                options.add_argument("--incognito")
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--ignore-ssl-errors")
                options.add_argument("--allow-running-insecure-content")
                options.add_argument("--remote-debugging-port=9222")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-logging")
                options.add_argument("--disable-default-apps")
                options.add_argument("--disable-sync")
                options.add_argument("--disable-translate")
                options.add_argument("--hide-scrollbars")
                options.add_argument("--mute-audio")
                options.add_argument("--no-first-run")
                options.add_argument("--safebrowsing-disable-auto-update")
                options.add_argument("--disable-client-side-phishing-detection")
                options.add_argument("--disable-component-update")
                options.add_argument("--disable-domain-reliability")
                options.add_argument("--disable-features=TranslateUI")
                options.add_argument("--disable-ipc-flooding-protection")
                
                # Disable automation detection
                options.add_experimental_option("useAutomationExtension", False)
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                options.add_experimental_option('useAutomationExtension', False)
                
                # Set up WebDriverManager
                cache_dir = "/tmp/chrome-session" if os.path.exists("/tmp") else os.path.join(os.getcwd(), "chrome-session")
                os.makedirs(cache_dir, exist_ok=True)
                
                # Set environment variables for WebDriverManager
                os.environ['WDM_LOCAL'] = '1'
                os.environ['WDM_CACHE_DIR'] = cache_dir
                os.environ['WDM_LOG_LEVEL'] = '0'  # Disable WebDriverManager logging
                
                # Try to get Chrome binary path
                chrome_binary = os.getenv('CHROME_BIN', '/usr/bin/google-chrome')
                if os.path.exists(chrome_binary):
                    options.binary_location = chrome_binary
                
                # Create service with WebDriverManager
                try:
                    # Try with regular Chrome first
                    service = Service(ChromeDriverManager(cache_valid_range=1).install())
                except Exception as e:
                    logger.warning(f"Failed to create ChromeDriver service: {e}")
                    # Fallback: try without cache validation
                    service = Service(ChromeDriverManager().install())
                
                # Create driver
                driver = webdriver.Chrome(service=service, options=options)
                
                # Test the driver
                driver.get("about:blank")
                driver.execute_script("return navigator.userAgent")
                
                logger.info("Chrome driver created successfully")
                return driver
                
            except SessionNotCreatedException as e:
                logger.warning(f"Session creation failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Clean up any partial driver instances
                    SeleniumUtils._cleanup_driver_resources()
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    logger.error(f"Failed to create Chrome driver after {max_retries} attempts")
                    raise
            except Exception as e:
                logger.warning(f"Unexpected error creating driver (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    SeleniumUtils._cleanup_driver_resources()
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"Failed to create Chrome driver after {max_retries} attempts")
                    raise SessionNotCreatedException(f"Failed to create Chrome driver: {e}")
    
    @staticmethod
    def _cleanup_driver_resources():
        """Clean up driver-related resources and processes."""
        try:
            # Kill any existing Chrome processes
            if os.name == 'nt':  # Windows
                os.system('taskkill /f /im chrome.exe 2>nul')
                os.system('taskkill /f /im chromedriver.exe 2>nul')
            else:  # Unix-like systems
                os.system('pkill -f chrome 2>/dev/null')
                os.system('pkill -f chromedriver 2>/dev/null')
            
            # Clean up temporary directories
            temp_dirs = ["/tmp/chrome-session", "chrome-session"]
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    @staticmethod
    def safe_quit_driver(driver: Optional[webdriver.Chrome]) -> bool:
        """
        Safely quit a WebDriver instance.
        
        Args:
            driver: WebDriver instance to quit
        
        Returns:
            True if quit successfully, False otherwise
        """
        if not driver:
            return True
            
        try:
            # Try to close all windows first
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                driver.close()
            
            # Then quit the driver
            driver.quit()
            logger.info("Driver quit successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Error quitting driver: {e}")
            try:
                # Force quit if normal quit fails
                driver.quit()
                return True
            except Exception:
                return False
    
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
