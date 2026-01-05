from app.scrapers.registry import scraper_registry
from app.scrapers.jobs_botswana import jobs_botswana_scraper

scraper_registry.register(jobs_botswana_scraper)

__all__ = ['scraper_registry', 'jobs_botswana_scraper']