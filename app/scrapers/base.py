from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup
import logging
from datetime import datetime

from app.models.job import (
    JobListing, JobListingsResponse, JobCategory, 
    JobLocation, JobType, PaginationInfo, SourceInfo
)
from app.scrapers.browser import browser_manager

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all job scrapers using Selenium."""
    
    def __init__(self):
        self._categories_cache: Optional[Tuple[List[JobCategory], datetime]] = None
        self._locations_cache: Optional[Tuple[List[JobLocation], datetime]] = None
        self._cache_ttl = 300  # 5 minutes
    
    @property
    @abstractmethod
    def source_id(self) -> str:
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        pass
    
    @property
    def description(self) -> str:
        return f"Job listings from {self.source_name}"
    
    @property
    def supported_filters(self) -> List[str]:
        return ["category", "location", "job_type", "page"]
    
    def get_source_info(self) -> SourceInfo:
        return SourceInfo(
            id=self.source_id,
            name=self.source_name,
            base_url=self.base_url,
            description=self.description,
            supported_filters=self.supported_filters,
            is_active=True
        )
    
    def fetch_page(self, url: str, wait_for_selector: str = None) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage using Selenium.
        
        Args:
            url: URL to fetch
            wait_for_selector: CSS selector to wait for before parsing
            
        Returns:
            BeautifulSoup object or None on error
        """
        logger.info(f"Fetching URL with Selenium: {url}")
        
        try:
            with browser_manager.get_driver() as driver:
                driver.get(url)
                
                # Wait for specific element if provided
                if wait_for_selector:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                    )
                else:
                    # Default wait for body
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                
                # Get page source
                html = driver.page_source
                logger.info(f"Page fetched successfully, content length: {len(html)}")
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                return soup
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise
    
    @abstractmethod
    def scrape_listings(
        self, 
        page: int = 1, 
        category: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> JobListingsResponse:
        pass
    
    @abstractmethod
    def scrape_job_detail(self, job_url: str) -> Optional[JobListing]:
        pass
    
    @abstractmethod
    def scrape_categories(self) -> List[JobCategory]:
        pass
    
    @abstractmethod
    def scrape_locations(self) -> List[JobLocation]:
        pass
    
    @abstractmethod
    def get_job_types(self) -> List[JobType]:
        pass
    
    def _is_cache_valid(self, cache_time: Optional[datetime]) -> bool:
        if cache_time is None:
            return False
        elapsed = (datetime.utcnow() - cache_time).total_seconds()
        return elapsed < self._cache_ttl
    
    def get_categories(self, force_refresh: bool = False) -> Tuple[List[JobCategory], bool]:
        if not force_refresh and self._categories_cache:
            categories, cache_time = self._categories_cache
            if self._is_cache_valid(cache_time):
                return categories, True
        
        categories = self.scrape_categories()
        self._categories_cache = (categories, datetime.utcnow())
        return categories, False
    
    def get_locations(self, force_refresh: bool = False) -> Tuple[List[JobLocation], bool]:
        if not force_refresh and self._locations_cache:
            locations, cache_time = self._locations_cache
            if self._is_cache_valid(cache_time):
                return locations, True
        
        locations = self.scrape_locations()
        self._locations_cache = (locations, datetime.utcnow())
        return locations, False