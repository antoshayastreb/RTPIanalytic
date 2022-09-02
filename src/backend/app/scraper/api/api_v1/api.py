from fastapi import APIRouter, Depends

from scraper.api.api_v1.endpoints import service, jobs
from scraper.utils.security import check_http_basic

api_router = APIRouter(dependencies=[Depends(check_http_basic)])
api_router.include_router(service.router, prefix="/service", tags=["service"])
api_router.include_router(jobs.router, prefix="/job", tags=["job"])