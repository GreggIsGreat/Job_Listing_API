from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.config import get_settings

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Import scrapers here to register them
    from app.scrapers.jobs_botswana import jobs_botswana_scraper
    from app.scrapers.registry import scraper_registry
    
    sources = scraper_registry.list_sources()
    logger.info(f"Registered job sources: {sources}")
    
    yield
    
    logger.info("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Botswana Job Listings API
    
    A powerful API for fetching job listings from various Botswana job websites.
    
    ### Features
    
    * 📋 **Job Listings** - Fetch job listings with pagination
    * 🔍 **Filtering** - Filter by category, location, and job type
    * 📍 **Locations** - Get available job locations with counts
    * 📁 **Categories** - Get available job categories with counts
    * 📄 **Job Details** - Get detailed information for specific jobs
    * ⚡ **Caching** - Categories and locations are cached for performance
    
    ### Supported Sources
    
    * **Jobs Botswana** - [jobsbotswana.info](https://jobsbotswana.info)
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Import and include routers after app is created
from app.routers import jobs
app.include_router(jobs.router)


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with basic information and links"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "API for fetching job listings from Botswana job websites",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "sources": "/api/v1/sources",
            "jobs_botswana": {
                "listings": "/api/v1/jobs/botswana",
                "detail": "/api/v1/jobs/botswana/detail",
                "categories": "/api/v1/jobs/botswana/categories",
                "locations": "/api/v1/jobs/botswana/locations",
                "job_types": "/api/v1/jobs/botswana/job-types"
            }
        },
        "examples": {
            "all_jobs": "/api/v1/jobs/botswana",
            "jobs_in_gaborone": "/api/v1/jobs/botswana?location=gaborone",
            "nursing_jobs": "/api/v1/jobs/botswana?category=nurse",
            "full_time_in_francistown": "/api/v1/jobs/botswana?location=francistown&job_type=full-time"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    from app.scrapers.registry import scraper_registry
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "registered_sources": scraper_registry.list_sources()
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR"
        }
    )