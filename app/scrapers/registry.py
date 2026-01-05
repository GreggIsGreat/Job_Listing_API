from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class ScraperRegistry:
    _instance = None
    _scrapers: Dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._scrapers = {}
        return cls._instance
    
    def register(self, scraper) -> None:
        source_id = scraper.source_id
        self._scrapers[source_id] = scraper
        logger.info(f"Registered scraper: {source_id}")
    
    def get(self, source_id: str):
        return self._scrapers.get(source_id)
    
    def get_all(self) -> Dict:
        return self._scrapers.copy()
    
    def get_source_info(self) -> List:
        return [s.get_source_info() for s in self._scrapers.values()]
    
    def list_sources(self) -> List[str]:
        return list(self._scrapers.keys())


scraper_registry = ScraperRegistry()