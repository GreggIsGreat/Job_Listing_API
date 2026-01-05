from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Service layer for job scraping operations.
    
    This provides a unified interface for accessing different job sources
    and handles common operations like caching and error handling.
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        from app.scrapers.registry import scraper_registry
        self.registry = scraper_registry
    
    def get_scraper(self, source_id: str):
        """Get a scraper by source ID"""
        return self.registry.get(source_id)
    
    def list_sources(self) -> List:
        """Get information about all available sources"""
        return self.registry.get_source_info()
    
    async def get_jobs(
        self,
        source_id: str,
        page: int = 1,
        category: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        keyword: Optional[str] = None
    ):
        """
        Get job listings from a specific source
        """
        scraper = self.get_scraper(source_id)
        if not scraper:
            raise ValueError(f"Unknown source: {source_id}")
        
        return await scraper.scrape_listings(
            page=page,
            category=category,
            location=location,
            job_type=job_type,
            keyword=keyword
        )
    
    async def get_job_detail(
        self,
        source_id: str,
        job_url: str
    ):
        """
        Get detailed job information
        """
        scraper = self.get_scraper(source_id)
        if not scraper:
            raise ValueError(f"Unknown source: {source_id}")
        
        return await scraper.scrape_job_detail(job_url)
    
    async def get_categories(
        self,
        source_id: str,
        force_refresh: bool = False
    ):
        """
        Get job categories from a specific source
        """
        from app.models.job import CategoriesResponse
        
        scraper = self.get_scraper(source_id)
        if not scraper:
            raise ValueError(f"Unknown source: {source_id}")
        
        categories, cached = await scraper.get_categories(force_refresh)
        
        return CategoriesResponse(
            success=True,
            message="Categories fetched successfully",
            data=categories,
            total_count=len(categories),
            source=scraper.source_name,
            cached=cached
        )
    
    async def get_locations(
        self,
        source_id: str,
        force_refresh: bool = False
    ):
        """
        Get job locations from a specific source
        """
        from app.models.job import LocationsResponse
        
        scraper = self.get_scraper(source_id)
        if not scraper:
            raise ValueError(f"Unknown source: {source_id}")
        
        locations, cached = await scraper.get_locations(force_refresh)
        
        return LocationsResponse(
            success=True,
            message="Locations fetched successfully",
            data=locations,
            total_count=len(locations),
            source=scraper.source_name,
            cached=cached
        )
    
    async def get_job_types(
        self,
        source_id: str
    ):
        """
        Get job types from a specific source
        """
        from app.models.job import JobTypesResponse
        
        scraper = self.get_scraper(source_id)
        if not scraper:
            raise ValueError(f"Unknown source: {source_id}")
        
        job_types = await scraper.get_job_types()
        
        return JobTypesResponse(
            success=True,
            message="Job types fetched successfully",
            data=job_types,
            total_count=len(job_types),
            source=scraper.source_name
        )


# Create the global service instance
scraper_service = ScraperService()