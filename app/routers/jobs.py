from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.models.job import (
    JobListingsResponse, JobDetailResponse,
    CategoriesResponse, LocationsResponse, JobTypesResponse,
    ErrorResponse, SourceInfo
)
from app.scrapers.jobs_botswana import jobs_botswana_scraper
from app.scrapers.registry import scraper_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Jobs"])


@router.get("/sources", response_model=List[SourceInfo])
def list_sources():
    """Get all available job sources"""
    return scraper_registry.get_source_info()


@router.get("/jobs/botswana", response_model=JobListingsResponse)
def get_jobs_botswana(
    page: int = Query(1, ge=1, le=100),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None)
):
    """Fetch job listings from jobsbotswana.info"""
    try:
        return jobs_botswana_scraper.scrape_listings(
            page=page, category=category, location=location, job_type=job_type
        )
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/detail", response_model=JobDetailResponse)
def get_job_detail(url: str = Query(...)):
    """Fetch job details"""
    try:
        job = jobs_botswana_scraper.scrape_job_detail(url)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobDetailResponse(success=True, message="Success", data=job, source=jobs_botswana_scraper.source_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/categories", response_model=CategoriesResponse)
def get_categories(refresh: bool = Query(False)):
    """Get job categories"""
    try:
        categories, cached = jobs_botswana_scraper.get_categories(refresh)
        return CategoriesResponse(
            success=True, message="Success", data=categories,
            total_count=len(categories), source=jobs_botswana_scraper.source_name, cached=cached
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/locations", response_model=LocationsResponse)
def get_locations(refresh: bool = Query(False)):
    """Get job locations"""
    try:
        locations, cached = jobs_botswana_scraper.get_locations(refresh)
        return LocationsResponse(
            success=True, message="Success", data=locations,
            total_count=len(locations), source=jobs_botswana_scraper.source_name, cached=cached
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/job-types", response_model=JobTypesResponse)
def get_job_types():
    """Get job types"""
    try:
        job_types = jobs_botswana_scraper.get_job_types()
        return JobTypesResponse(
            success=True, message="Success", data=job_types,
            total_count=len(job_types), source=jobs_botswana_scraper.source_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))