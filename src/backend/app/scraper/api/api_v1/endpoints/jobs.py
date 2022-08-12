from fastapi import APIRouter, Depends, HTTPException, status
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scraper.utils.services.scheduler_service.scheduler import get_scheduler
from scraper.schemas.job import (
    CurrentScheduledJobsResponse,
    CurrentScheduledJob,
    JobCreateDeleteResponse
)
from scraper.utils.exeption_handlers.scheduler import (
    JobNotFoundException
)

router = APIRouter()

@router.get("/all_scheduled", response_model=CurrentScheduledJobsResponse)
async def get_all_scheduled_jobs(
    scheduler: AsyncIOScheduler = Depends(get_scheduler)
):
    """Получить все запланированые задачи"""
    try:
        scheduled_jobs = [CurrentScheduledJob]
        for job in scheduler.get_jobs():
            scheduled_jobs.append(
                CurrentScheduledJob(
                    job_id=str(job.id),
                    description=str(job.name),
                    next_run=str(job.next_run_time),
                    run_frequency=str(job.trigger)
                )
            )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")

@router.delete("/delete/{job_id}", response_model=JobCreateDeleteResponse)
async def delete_job(
    job_id: str,
    scheduler: AsyncIOScheduler = Depends(get_scheduler)
):
    """Удалить задачу"""
    if not scheduler.get_job(job_id):
        raise JobNotFoundException()
    try:
        scheduler.remove_job(job_id)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"При удалени задачи возникла ошибка {str(ex)}")