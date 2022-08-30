from fastapi import APIRouter

from scraper.api.api_v1.endpoints import service, jobs

api_router = APIRouter()
api_router.include_router(service.router, prefix="/service", tags=["service"])
api_router.include_router(jobs.router, prefix="/job", tags=["job"])