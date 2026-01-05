from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.config import get_settings

# Configure logging
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
    
    from app.scrapers import scraper_registry
    logger.info(f"Registered sources: {scraper_registry.list_sources()}")
    
    yield
    
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="API for fetching job listings from Botswana job websites using Selenium",
    version=settings.app_version,
    lifespan=lifespan,
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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 3))
    return response


from app.routers import jobs
app.include_router(jobs.router)


@app.get("/", tags=["Root"])
def root():
    """API root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "jobs": "/api/v1/jobs/botswana",
            "categories": "/api/v1/jobs/botswana/categories",
            "locations": "/api/v1/jobs/botswana/locations",
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    from app.scrapers import scraper_registry
    return {
        "status": "healthy",
        "sources": scraper_registry.list_sources()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": str(exc)}
    )