from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Supported job source websites"""
    JOBS_BOTSWANA = "jobsbotswana"
    # Future sources can be added here
    # CAREERS_BW = "careersbw"
    # INDEED_BW = "indeedbw"


class JobListing(BaseModel):
    """Model representing a single job listing"""
    id: Optional[str] = Field(None, description="Unique identifier for the job")
    title: str = Field(..., description="Job title")
    url: str = Field(..., description="Direct URL to the job posting")
    company: Optional[str] = Field(None, description="Company name")
    job_type: Optional[str] = Field(None, description="Type of employment")
    location: Optional[str] = Field(None, description="Job location")
    closing_date: Optional[str] = Field(None, description="Application closing date")
    posted_date: Optional[str] = Field(None, description="Date the job was posted")
    category: Optional[str] = Field(None, description="Job category")
    posted_ago: Optional[str] = Field(None, description="Human-readable time since posting")
    description: Optional[str] = Field(None, description="Job description excerpt")
    is_closed: bool = Field(False, description="Whether the job posting is closed")
    source: str = Field(..., description="Source website")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When the job was scraped")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "98870",
                "title": "GRADUATE PROGRAMME – Bryte Insurance Company Limited",
                "url": "https://jobsbotswana.info/jobs/graduate-programme-bryte-insurance-company-limited/",
                "company": "Bryte Insurance Company Limited",
                "job_type": "Full Time",
                "location": "Gaborone",
                "closing_date": "January 10, 2026",
                "category": "Graduate Programme",
                "posted_ago": "4 days ago",
                "is_closed": False,
                "source": "jobsbotswana.info"
            }
        }


class JobCategory(BaseModel):
    """Model representing a job category"""
    slug: str = Field(..., description="URL-friendly category identifier")
    name: str = Field(..., description="Display name of the category")
    count: int = Field(0, description="Number of jobs in this category")
    url: Optional[str] = Field(None, description="Direct URL to category listing")


class JobLocation(BaseModel):
    """Model representing a job location"""
    slug: str = Field(..., description="URL-friendly location identifier")
    name: str = Field(..., description="Display name of the location")
    count: int = Field(0, description="Number of jobs in this location")
    description: Optional[str] = Field(None, description="Location description")
    url: Optional[str] = Field(None, description="Direct URL to location listing")


class JobType(BaseModel):
    """Model representing a job type"""
    slug: str = Field(..., description="URL-friendly job type identifier")
    name: str = Field(..., description="Display name of the job type")
    count: int = Field(0, description="Number of jobs of this type")


class PaginationInfo(BaseModel):
    """Pagination metadata"""
    current_page: int
    total_pages: int
    total_jobs: int
    jobs_per_page: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None


class JobListingsResponse(BaseModel):
    """Response model for job listings endpoint"""
    success: bool = True
    message: str = "Jobs fetched successfully"
    data: List[JobListing]
    pagination: PaginationInfo
    filters_applied: dict = Field(default_factory=dict)
    source: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class JobDetailResponse(BaseModel):
    """Response model for single job detail"""
    success: bool = True
    message: str = "Job details fetched successfully"
    data: JobListing
    source: str


class CategoriesResponse(BaseModel):
    """Response model for categories endpoint"""
    success: bool = True
    message: str = "Categories fetched successfully"
    data: List[JobCategory]
    total_count: int
    source: str
    cached: bool = False


class LocationsResponse(BaseModel):
    """Response model for locations endpoint"""
    success: bool = True
    message: str = "Locations fetched successfully"
    data: List[JobLocation]
    total_count: int
    source: str
    cached: bool = False


class JobTypesResponse(BaseModel):
    """Response model for job types endpoint"""
    success: bool = True
    message: str = "Job types fetched successfully"
    data: List[JobType]
    total_count: int
    source: str


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


class SourceInfo(BaseModel):
    """Information about a job source"""
    id: str
    name: str
    base_url: str
    description: Optional[str] = None
    supported_filters: List[str] = []
    is_active: bool = True