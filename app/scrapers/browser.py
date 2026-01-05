import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Selenium browser instances."""
    
    def __init__(self):
        self.chrome_options = self._get_chrome_options()
    
    def _get_chrome_options(self) -> Options:
        """Configure Chrome options for headless scraping."""
        options = Options()
        
        # Run headless (no GUI)
        options.add_argument("--headless=new")
        
        # Disable GPU (required for headless on some systems)
        options.add_argument("--disable-gpu")
        
        # Disable sandbox (required for Docker/Linux)
        options.add_argument("--no-sandbox")
        
        # Disable dev shm usage (prevents crashes in Docker)
        options.add_argument("--disable-dev-shm-usage")
        
        # Set window size
        options.add_argument("--window-size=1920,1080")
        
        # Disable images for faster loading
        options.add_argument("--blink-settings=imagesEnabled=false")
        
        # User agent
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Disable logging
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        return options
    
    def create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome WebDriver instance."""
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logger.error(f"Failed to create Chrome driver: {e}")
            raise
    
    @contextmanager
    def get_driver(self):
        """Context manager for WebDriver - ensures proper cleanup."""
        driver = None
        try:
            driver = self.create_driver()
            yield driver
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f"Error closing driver: {e}")


# Global browser manager instance
browser_manager = BrowserManager()