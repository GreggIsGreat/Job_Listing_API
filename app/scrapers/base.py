from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
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
    """
    Abstract base class for all job scrapers.
    
    To add a new job source:
    1. Create a new class that inherits from BaseScraper
    2. Implement all abstract methods
    3. Register the scraper in the registry
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.timeout = 30.0
        self._categories_cache: Optional[Tuple[List[JobCategory], datetime]] = None
        self._locations_cache: Optional[Tuple[List[JobLocation], datetime]] = None
        self._cache_ttl = 300  # 5 minutes
    
    @property
    @abstractmethod
    def source_id(self) -> str:
        """Return unique identifier for the source"""
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the display name of the job source"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL of the job site"""
        pass
    
    @property
    def description(self) -> str:
        """Return a description of the job source"""
        return f"Job listings from {self.source_name}"
    
    @property
    def supported_filters(self) -> List[str]:
        """Return list of supported filter types"""
        return ["category", "location", "job_type", "page"]
    
    def get_source_info(self) -> SourceInfo:
        """Get information about this source"""
        return SourceInfo(
            id=self.source_id,
            name=self.source_name,
            base_url=self.base_url,
            description=self.description,
            supported_filters=self.supported_filters,
            is_active=True
        )
    
    @abstractmethod
    async def scrape_listings(
        self, 
        page: int = 1, 
        category: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> JobListingsResponse:
        """
        Scrape job listings from the source.
        
        Args:
            page: Page number to scrape
            category: Filter by job category slug
            location: Filter by location slug
            job_type: Filter by job type slug
            keyword: Search keyword
        
        Returns:
            JobListingsResponse with list of jobs and pagination info
        """
        pass
    
    @abstractmethod
    async def scrape_job_detail(self, job_url: str) -> Optional[JobListing]:
        """
        Scrape detailed information for a single job.
        
        Args:
            job_url: Full URL to the job posting
        
        Returns:
            JobListing with detailed information or None if not found
        """
        pass
    
    @abstractmethod
    async def scrape_categories(self) -> List[JobCategory]:
        """
        Scrape available job categories from the source.
        
        Returns:
            List of JobCategory objects with counts
        """
        pass
    
    @abstractmethod
    async def scrape_locations(self) -> List[JobLocation]:
        """
        Scrape available job locations from the source.
        
        Returns:
            List of JobLocation objects with counts
        """
        pass
    
    @abstractmethod
    async def get_job_types(self) -> List[JobType]:
        """
        Get available job types.
        
        Returns:
            List of JobType objects
        """
        pass
    
    async def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None on error
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, 
                follow_redirects=True
            ) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'lxml')
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            raise
    
    def _is_cache_valid(self, cache_time: Optional[datetime]) -> bool:
        """Check if cached data is still valid"""
        if cache_time is None:
            return False
        elapsed = (datetime.utcnow() - cache_time).total_seconds()
        return elapsed < self._cache_ttl
    
    async def get_categories(self, force_refresh: bool = False) -> Tuple[List[JobCategory], bool]:
        """
        Get categories with caching.
        
        Returns:
            Tuple of (categories list, was_cached boolean)
        """
        if not force_refresh and self._categories_cache:
            categories, cache_time = self._categories_cache
            if self._is_cache_valid(cache_time):
                return categories, True
        
        categories = await self.scrape_categories()
        self._categories_cache = (categories, datetime.utcnow())
        return categories, False
    
    async def get_locations(self, force_refresh: bool = False) -> Tuple[List[JobLocation], bool]:
        """
        Get locations with caching.
        
        Returns:
            Tuple of (locations list, was_cached boolean)
        """
        if not force_refresh and self._locations_cache:
            locations, cache_time = self._locations_cache
            if self._is_cache_valid(cache_time):
                return locations, True
        
        locations = await self.scrape_locations()
        self._locations_cache = (locations, datetime.utcnow())
        return locations, False