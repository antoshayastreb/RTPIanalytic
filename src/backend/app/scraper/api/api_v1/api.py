from fastapi import APIRouter, Depends

from scraper.config import settings
from scraper.api.api_v1.endpoints import service, jobs, info
from scraper.security import check_http_basic

use_auth = settings.ENABLE_AUTH.lower() == 'true'

api_router = APIRouter(
    dependencies= [Depends(check_http_basic)] if use_auth  else None
)
api_router.include_router(service.router, prefix="/service", tags=["service"])
api_router.include_router(jobs.router, prefix="/job", tags=["job"])
api_router.include_router(info.router, prefix="/info", tags=["info"])