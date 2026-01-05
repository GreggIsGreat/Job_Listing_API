from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.models.job import (
    JobListingsResponse, JobDetailResponse, 
    CategoriesResponse, LocationsResponse, JobTypesResponse,
    ErrorResponse, SourceInfo
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Jobs"])


def get_scraper_service():
    """Get scraper service instance"""
    from app.services.scraper_service import scraper_service
    return scraper_service


# ============== Source Management ==============

@router.get(
    "/sources",
    response_model=List[SourceInfo],
    summary="List Available Sources",
    description="Get a list of all available job sources"
)
async def list_sources():
    """Get all available job sources"""
    service = get_scraper_service()
    return service.list_sources()


# ============== Jobs Botswana Endpoints ==============

@router.get(
    "/jobs/botswana",
    response_model=JobListingsResponse,
    responses={
        200: {"description": "Successfully fetched job listings"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get Jobs from Jobs Botswana",
    description="""
    Fetch job listings from jobsbotswana.info with optional filters.
    
    **Filtering:**
    - Use `category` to filter by job category (e.g., 'nurse', 'driver', 'teacher')
    - Use `location` to filter by location (e.g., 'gaborone', 'francistown', 'maun')
    - Use `job_type` to filter by employment type (e.g., 'full-time', 'contract')
    
    **Pagination:**
    - Use `page` parameter to navigate through results (15 jobs per page)
    """
)
async def get_jobs_botswana(
    page: int = Query(1, ge=1, le=100, description="Page number"),
    category: Optional[str] = Query(
        None, 
        description="Filter by job category slug (e.g., 'nurse', 'driver')"
    ),
    location: Optional[str] = Query(
        None, 
        description="Filter by location slug (e.g., 'gaborone', 'francistown')"
    ),
    job_type: Optional[str] = Query(
        None, 
        description="Filter by job type slug (e.g., 'full-time', 'contract')"
    )
):
    """Fetch job listings from jobsbotswana.info"""
    try:
        service = get_scraper_service()
        result = await service.get_jobs(
            source_id="jobsbotswana",
            page=page,
            category=category,
            location=location,
            job_type=job_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e), "error_code": "SCRAPING_ERROR"}
        )


@router.get(
    "/jobs/botswana/detail",
    response_model=JobDetailResponse,
    responses={
        200: {"description": "Successfully fetched job details"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get Job Details",
    description="Fetch detailed information for a specific job posting"
)
async def get_job_detail(
    url: str = Query(..., description="Full URL of the job posting")
):
    """Fetch detailed information for a specific job posting."""
    try:
        service = get_scraper_service()
        job = await service.get_job_detail(
            source_id="jobsbotswana",
            job_url=url
        )
        if not job:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "message": "Job not found", "error_code": "NOT_FOUND"}
            )
        
        scraper = service.get_scraper("jobsbotswana")
        return JobDetailResponse(
            success=True,
            message="Job details fetched successfully",
            data=job,
            source=scraper.source_name if scraper else "Jobs Botswana"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job detail: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e), "error_code": "SCRAPING_ERROR"}
        )


@router.get(
    "/jobs/botswana/categories",
    response_model=CategoriesResponse,
    summary="Get Job Categories",
    description="Get list of available job categories with job counts."
)
async def get_categories(
    refresh: bool = Query(False, description="Force refresh cache")
):
    """Get available job categories with counts."""
    try:
        service = get_scraper_service()
        result = await service.get_categories(
            source_id="jobsbotswana",
            force_refresh=refresh
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e), "error_code": "SCRAPING_ERROR"}
        )


@router.get(
    "/jobs/botswana/locations",
    response_model=LocationsResponse,
    summary="Get Job Locations",
    description="Get list of available job locations with job counts."
)
async def get_locations(
    refresh: bool = Query(False, description="Force refresh cache")
):
    """Get available job locations with counts."""
    try:
        service = get_scraper_service()
        result = await service.get_locations(
            source_id="jobsbotswana",
            force_refresh=refresh
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e), "error_code": "SCRAPING_ERROR"}
        )


@router.get(
    "/jobs/botswana/job-types",
    response_model=JobTypesResponse,
    summary="Get Job Types",
    description="Get list of available job types for filtering"
)
async def get_job_types():
    """Get available job types."""
    try:
        service = get_scraper_service()
        result = await service.get_job_types(source_id="jobsbotswana")
        return result
    except Exception as e:
        logger.error(f"Error fetching job types: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e), "error_code": "SCRAPING_ERROR"}
        )