import uuid
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.job import Job as APSJob
from typing import List

from scraper.utils.services.scheduler_service import scheduler_service
from scraper.schemas.job import (
    CurrentScheduledJobsResponse,
    CurrentScheduledJob,
    JobCreateDeleteResponse,
    JobOut
)
from scraper.utils.exeption_handlers.scheduler import (
    JobNotFoundException
)
from scraper.utils.services.scheduler_service.scraper_methods import (
    update_wraper,
    update_all_wraper,
    test_job_main
)

from scraper.config import settings
from scraper.utils.help_func import JobHelper

router = APIRouter()

@router.get("/all_scheduled", response_model=CurrentScheduledJobsResponse)
async def get_all_scheduled_jobs(
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler)
):
    """Получить все запланированые задачи"""
    try:
        scheduled_jobs = [CurrentScheduledJob]
        for job in scheduler.get_jobs():
            scheduled_jobs.append(
                CurrentScheduledJob(
                    job_id=str(job.id),
                    name=str(job.name),
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
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler)
):
    """Удалить задачу"""
    if not scheduler.get_job(job_id):
        raise JobNotFoundException(job_id)
    try:
        scheduler.remove_job(job_id)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"При удалени задачи возникла ошибка {str(ex)}")

@router.get("/update_all", response_model=JobOut)
async def update_all_tables(
    fetch_all: bool = False,
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler)
):
    """Обновить все таблицы вручную"""
    try:
        id = str(uuid.uuid4())
        job: APSJob = scheduler.add_job(
            update_all_wraper,
            id = id,
            name = 'Oбновление всех таблиц' + 
            'полное' if fetch_all else 'с последней даты',
            args=[fetch_all, id]
        )
        return JobOut(
            job_id=job.id,
            name=job.name
        )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")
    

@router.get("/update/{table}", response_model=JobOut)
async def update_table_job(
    table: str,
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler)
):
    """Обновить указанную таблицу"""
    try:
        id = str(uuid.uuid4())
        job: APSJob = scheduler.add_job(
            update_wraper,
            id=id, 
            name=f"Обновление {table}", 
            args=[table, id]
        )
        return JobOut(
            job_id=job.id,
            name=job.name
        )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")

@router.get("/test_coroutine", response_model=JobOut)
async def test_for_coroutine(
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler)
):
    try:
        id = str(uuid.uuid4())
        job = scheduler.add_job(
            test_job_main,
            id=id,
            misfire_grace_time=None,
            args=[id]
        )
        return JobOut(
            job_id=job.id,
            name=job.name
        )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")