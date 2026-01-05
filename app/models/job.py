from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobListing(BaseModel):
    id: Optional[str] = None
    title: str
    url: str
    company: Optional[str] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    closing_date: Optional[str] = None
    posted_date: Optional[str] = None
    category: Optional[str] = None
    posted_ago: Optional[str] = None
    description: Optional[str] = None
    is_closed: bool = False
    source: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class JobCategory(BaseModel):
    slug: str
    name: str
    count: int = 0
    url: Optional[str] = None


class JobLocation(BaseModel):
    slug: str
    name: str
    count: int = 0
    description: Optional[str] = None
    url: Optional[str] = None


class JobType(BaseModel):
    slug: str
    name: str
    count: int = 0


class PaginationInfo(BaseModel):
    current_page: int
    total_pages: int
    total_jobs: int
    jobs_per_page: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None


class JobListingsResponse(BaseModel):
    success: bool = True
    message: str = "Jobs fetched successfully"
    data: List[JobListing]
    pagination: PaginationInfo
    filters_applied: dict = Field(default_factory=dict)
    source: str
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class JobDetailResponse(BaseModel):
    success: bool = True
    message: str = "Job details fetched successfully"
    data: JobListing
    source: str


class CategoriesResponse(BaseModel):
    success: bool = True
    message: str = "Categories fetched successfully"
    data: List[JobCategory]
    total_count: int
    source: str
    cached: bool = False


class LocationsResponse(BaseModel):
    success: bool = True
    message: str = "Locations fetched successfully"
    data: List[JobLocation]
    total_count: int
    source: str
    cached: bool = False


class JobTypesResponse(BaseModel):
    success: bool = True
    message: str = "Job types fetched successfully"
    data: List[JobType]
    total_count: int
    source: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None


class SourceInfo(BaseModel):
    id: str
    name: str
    base_url: str
    description: Optional[str] = None
    supported_filters: List[str] = []
    is_active: bool = True