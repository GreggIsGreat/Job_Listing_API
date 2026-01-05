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


@router.get("/sources", response_model=List[SourceInfo], summary="List Available Sources")
def list_sources():
    return scraper_registry.get_source_info()


@router.get(
    "/jobs/botswana",
    response_model=JobListingsResponse,
    summary="Get Jobs from Jobs Botswana"
)
def get_jobs_botswana(
    page: int = Query(1, ge=1, le=100, description="Page number"),
    category: Optional[str] = Query(None, description="Filter by job category slug"),
    location: Optional[str] = Query(None, description="Filter by location slug"),
    job_type: Optional[str] = Query(None, description="Filter by job type slug")
):
    """Fetch job listings from jobsbotswana.info"""
    try:
        logger.info(f"API Request: page={page}, category={category}, location={location}, job_type={job_type}")
        result = jobs_botswana_scraper.scrape_listings(
            page=page,
            category=category,
            location=location,
            job_type=job_type
        )
        logger.info(f"API Response: {len(result.data)} jobs returned")
        return result
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/detail", response_model=JobDetailResponse, summary="Get Job Details")
def get_job_detail(url: str = Query(..., description="Full URL of the job posting")):
    try:
        job = jobs_botswana_scraper.scrape_job_detail(url)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobDetailResponse(
            success=True,
            message="Job details fetched successfully",
            data=job,
            source=jobs_botswana_scraper.source_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/categories", response_model=CategoriesResponse, summary="Get Job Categories")
def get_categories(refresh: bool = Query(False, description="Force refresh cache")):
    try:
        categories, cached = jobs_botswana_scraper.get_categories(refresh)
        return CategoriesResponse(
            success=True,
            message="Categories fetched successfully",
            data=categories,
            total_count=len(categories),
            source=jobs_botswana_scraper.source_name,
            cached=cached
        )
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/locations", response_model=LocationsResponse, summary="Get Job Locations")
def get_locations(refresh: bool = Query(False, description="Force refresh cache")):
    try:
        locations, cached = jobs_botswana_scraper.get_locations(refresh)
        return LocationsResponse(
            success=True,
            message="Locations fetched successfully",
            data=locations,
            total_count=len(locations),
            source=jobs_botswana_scraper.source_name,
            cached=cached
        )
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/botswana/job-types", response_model=JobTypesResponse, summary="Get Job Types")
def get_job_types():
    try:
        job_types = jobs_botswana_scraper.get_job_types()
        return JobTypesResponse(
            success=True,
            message="Job types fetched successfully",
            data=job_types,
            total_count=len(job_types),
            source=jobs_botswana_scraper.source_name
        )
    except Exception as e:
        logger.error(f"Error fetching job types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))