from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scraper.utils.services.scheduler_service import scheduler_service
from scraper.schemas.job import (
    CurrentScheduledJobsResponse,
    CurrentScheduledJob,
    JobCreateDeleteResponse
)
from scraper.utils.exeption_handlers.scheduler import (
    JobNotFoundException
)
from scraper.utils.services.scheduler_service.scraper_methods import (
    update_wraper,
    test_job_wrapper
)

from scraper.config import settings
from scraper.utils.help_func import JobHelper

router = APIRouter()

@router.get("/all_scheduled", response_model=CurrentScheduledJobsResponse)
async def get_all_scheduled_jobs(
    scheduler: AsyncIOScheduler = Depends(scheduler_service.get_scheduler)
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
    scheduler: AsyncIOScheduler = Depends(scheduler_service.get_scheduler)
):
    """Удалить задачу"""
    if not scheduler.get_job(job_id):
        raise JobNotFoundException(job_id)
    try:
        scheduler.remove_job(job_id)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"При удалени задачи возникла ошибка {str(ex)}")

@router.get("/update/{table}")
async def update_table_job(
    table: str,
    scheduler: AsyncIOScheduler = Depends(scheduler_service.get_scheduler)
):
    """Обновить указанную таблицу"""
    try:
        scheduler.add_job(
            update_wraper, 
            name=f"Обновление {table}", 
            args=[table]
        )
        #await get_table_count(table)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")

@router.get("/test_coroutine")
async def test_for_coroutine(
    scheduler: AsyncIOScheduler = Depends(scheduler_service.get_scheduler)
):
    try:
        max = 10
        main_args_list = [
            i for i in range (0, 100)
        ]
        splited_list = JobHelper.split_list(main_args_list, max)
        for inner_list in splited_list:
            scheduler.add_job(
                test_job_wrapper,
                #max_instances=2,
                misfire_grace_time=None,
                args=[inner_list, 3]
            )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")