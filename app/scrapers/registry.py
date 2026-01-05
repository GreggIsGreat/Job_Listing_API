from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class ScraperRegistry:
    """
    Registry for managing multiple job scrapers.
    """
    
    _scrapers: Dict = {}
    
    def register(self, scraper) -> None:
        """
        Register a new scraper.
        """
        source_id = scraper.source_id
        if source_id in self._scrapers:
            logger.warning(f"Scraper {source_id} already registered, overwriting")
        
        self._scrapers[source_id] = scraper
        logger.info(f"Registered scraper: {source_id} ({scraper.source_name})")
    
    def get(self, source_id: str):
        """
        Get a scraper by source ID.
        """
        return self._scrapers.get(source_id)
    
    def get_all(self) -> Dict:
        """Get all registered scrapers"""
        return self._scrapers.copy()
    
    def get_source_info(self) -> List:
        """Get information about all registered sources"""
        return [scraper.get_source_info() for scraper in self._scrapers.values()]
    
    def list_sources(self) -> List[str]:
        """Get list of all registered source IDs"""
        return list(self._scrapers.keys())


# Global registry instance
scraper_registry = ScraperRegistry()