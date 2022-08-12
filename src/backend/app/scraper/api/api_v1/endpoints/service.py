from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import (
    STATE_PAUSED,
    STATE_STOPPED,
    STATE_RUNNING
)

from scraper.utils.services.scheduler_service.scheduler import get_scheduler
from scraper.utils.exeption_handlers.scheduler import (
    SchedulerAlreadyPausedException,
    SchedulerAlreadyRunningException,
    SchedulerStopedException
)

router = APIRouter()


@router.post("/pause", status_code=200)
async def pause_scheduler(scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    """Приостановка шедулера"""
    if scheduler.state == STATE_STOPPED:
        raise SchedulerStopedException()
    if scheduler.state == STATE_PAUSED:
        raise SchedulerAlreadyPausedException()
    try:
        scheduler.pause()
        return JSONResponse(
            content={"message" : "Шедулер успешно приостановлен"}
        )
    except Exception as e:
        raise HTTPException(status_code=409, 
        detail=f"Не удалось приостановить шедулер {e}")

@router.post("/resume", status_code=200)
async def resume_scheduler(scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    """Возобновление работы шедулера"""
    if scheduler.state == STATE_STOPPED:
        raise SchedulerStopedException()
    if scheduler.state == STATE_RUNNING:
        raise SchedulerAlreadyRunningException()
    try:
        scheduler.resume()
        return JSONResponse(
            content={"message" : "Шедулер возобновлен"}
        )
    except Exception as e:
        raise HTTPException(status_code=409,
        detail=f"Не удалось возобновить шедулер: {str(e)}")