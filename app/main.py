from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings
from app.routers import jobs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API for fetching job listings from Botswana job websites",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register scrapers
from app.scrapers import scraper_registry
logger.info(f"Registered sources: {scraper_registry.list_sources()}")

app.include_router(jobs.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "jobs": "/api/v1/jobs/botswana",
            "categories": "/api/v1/jobs/botswana/categories",
            "locations": "/api/v1/jobs/botswana/locations",
            "job_types": "/api/v1/jobs/botswana/job-types",
        }
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "sources": scraper_registry.list_sources()}


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"success": False, "message": str(exc)})