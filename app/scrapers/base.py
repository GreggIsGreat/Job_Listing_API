from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import httpx
from bs4 import BeautifulSoup
import logging
from datetime import datetime

from app.models.job import (
    JobListing, JobListingsResponse, JobCategory, 
    JobLocation, JobType, PaginationInfo, SourceInfo
)

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.timeout = 30.0
        self._categories_cache: Optional[Tuple[List[JobCategory], datetime]] = None
        self._locations_cache: Optional[Tuple[List[JobLocation], datetime]] = None
        self._cache_ttl = 300
    
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
    
    def fetch_page_sync(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage using synchronous httpx."""
        logger.info(f"Fetching URL: {url}")
        
        try:
            # Use synchronous client
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                
                html_content = response.text
                logger.info(f"Received {len(html_content)} bytes")
                
                # Try lxml first, fall back to html.parser
                try:
                    soup = BeautifulSoup(html_content, 'lxml')
                except Exception:
                    logger.warning("lxml failed, using html.parser")
                    soup = BeautifulSoup(html_content, 'html.parser')
                
                return soup
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
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