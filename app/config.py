from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "Botswana Job Listings API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Scraping settings
    request_timeout: float = 30.0
    cache_ttl: int = 300  # 5 minutes cache for categories/locations
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()