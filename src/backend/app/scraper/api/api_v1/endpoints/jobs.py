import uuid
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.job import Job as APSJob
from typing import List
from sqlalchemy.orm import Session

from scraper.utils.services.scheduler_service import scheduler_service
from scraper.schemas.job import (
    CurrentScheduledJobsResponse,
    CurrentScheduledJob,
    JobCreateDeleteResponse,
    JobOut,
    JobOutExtendedInfo
)
from scraper.utils.exeption_handlers.scheduler import (
    JobNotFoundException
)
from scraper.utils.services.scheduler_service.scraper_methods import (
    update_wraper,
    update_all_wraper,
    test_job_main,
    jobs_clean_up
)

from scraper.config import settings
from scraper.utils.help_func import JobHelper
from scraper.db.session import get_session, get_sync_session
from scraper.crud.jobs import job_crud

router = APIRouter(
    dependencies=[Depends(scheduler_service.scheduler_running_check)]
)

@router.get("/{job_id}/basic_info", response_model=JobOut)
async def get_job_basic_info(
    job_id: str,
    session=Depends(get_sync_session)
):
    """Получить базовую информацию по задаче из базы"""
    job = job_crud.get(session, job_id)
    if not job:
        raise JobNotFoundException(job_id)
    return job

@router.get("/{job_id}/extended_info", response_model=JobOutExtendedInfo)
async def get_job_extended_info(
    job_id: str,
    session=Depends(get_sync_session)
):
    """Получить полную информацию по задаче из базы"""
    job = job_crud.get_job_extended_info(session, job_id)
    if not job:
        raise JobNotFoundException(job_id)
    return job


# @router.get("/all_scheduled", response_model=CurrentScheduledJobsResponse)
# async def get_all_scheduled_jobs(
#     scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler)
# ):
#     """Получить все запланированые задачи"""
#     try:
#         scheduled_jobs = [CurrentScheduledJob]
#         for job in scheduler.get_jobs():
#             scheduled_jobs.append(
#                 CurrentScheduledJob(
#                     job_id=str(job.id),
#                     name=str(job.name),
#                     next_run=str(job.next_run_time),
#                     run_frequency=str(job.trigger)
#                 )
#             )
#     except Exception as ex:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         detail=f"Возникла ошибка: {str(ex)}")

# @router.delete("/delete/{job_id}", response_model=JobCreateDeleteResponse)
# async def delete_job(
#     job_id: str,
#     scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler)
# ):
#     """Удалить задачу"""
#     if not scheduler.get_job(job_id):
#         raise JobNotFoundException(job_id)
#     try:
#         scheduler.remove_job(job_id)
#     except Exception as ex:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         detail=f"При удалени задачи возникла ошибка {str(ex)}")

@router.get("/update_all", response_model=JobOut)
async def update_all_tables(
    fetch_all: bool = False,
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler),
    session: Session = Depends(get_sync_session)
):
    """Обновить все таблицы вручную"""
    try:
        id = str(uuid.uuid4())
        scheduler.add_job(
            update_all_wraper,
            id = id,
            name = f'Oбновление всех таблиц {"полное" if fetch_all else "с последней даты"}',
            args=[fetch_all, id]
        )
        return job_crud.get(session, id)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")
    

@router.get("/update/{table}", response_model=JobOut)
async def update_table_job(
    table: str,
    fetch_all: bool = False,
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler),
    session: Session = Depends(get_sync_session)
):
    """Обновить указанную таблицу"""
    try:
        id = str(uuid.uuid4())
        scheduler.add_job(
            update_wraper,
            id=id, 
            name=f"Обновление {table}", 
            args=[table, id, fetch_all]
        )
        return job_crud.get(session, id)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")

@router.get("/test_coroutine", response_model=JobOut)
async def test_for_coroutine(
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler),
    session: Session = Depends(get_sync_session)
):
    try:
        id = str(uuid.uuid4())
        scheduler.add_job(
            test_job_main,
            id=id,
            misfire_grace_time=None,
            args=[id]
        )
        return job_crud.get(session, id)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")

@router.get("/clean_up_jobs", response_model=JobOut)
async def clean_up_jobs(
    scheduler: BaseScheduler = Depends(scheduler_service.get_scheduler),
    session: Session = Depends(get_sync_session)    
):
    """Удалить застывшие задачи"""
    try:
        id = str(uuid.uuid4())
        scheduler.add_job(
            jobs_clean_up,
            name="Очистка задач",
            id=id,
            misfire_grace_time=None
        )
        return job_crud.get(session, id)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")
