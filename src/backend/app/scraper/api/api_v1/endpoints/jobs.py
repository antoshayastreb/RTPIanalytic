import uuid
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.job import Job as APSJob
from typing import List, Optional, Any, Union
from sqlalchemy.orm import Session

#from scraper.utils.services.scheduler_service import scheduler_service

from scraper.scheduler_service import scheduler_service
from scraper.scheduler_service.jobs.rtpi import (
    __spawn_get_data_jobs_job,
    create_update_table_job
) 

from scraper.models import (
    Table
)
from scraper.schemas.job import (
    JobOut,
    JobOutExtendedInfo,
    JobScheduledResponse
)

from scraper.schemas.schedules import (
    Interval,
    Date,
    Cron
)

# from scraper.scheduler_service.exceptions import (
#     JobNotFoundException
# )


from scraper.config import settings
# from scraper.utils.help_func import JobHelper
# from scraper.db.session import get_session, get_sync_session
# from scraper.crud.jobs import job_crud

#Dependecies

#Планирование
async def schedules(
    interval_schedule: Union[Interval, None] = None,
    date_schedule: Union[Date, None] = None,
    cron_schedule: Union[Cron, None] = None
):
    """
    Получить варианты планирования расписания выполнения задач.
    """
    return {
        "interval_schedule": interval_schedule,
        "date_schedule": date_schedule,
        "cron_schedule": cron_schedule
    }

router = APIRouter(
    #dependencies=[Depends(scheduler_service.scheduler_running_check)]
)

@router.post(
    "/update/{table}",
)
async def update_table_job(
    table: Table,
    fetch_all: bool = False,
    #schedules: dict = Depends(schedules),
    hard_filter: str = None,
    #scheduler: BaseScheduler = Depends(scheduler_service.instance)
):
    """Обновить указанную таблицу"""
    try:
        scheduler_service.instance.add_job(
            create_update_table_job,
            name=f'update_table_job_{table.value}',
            args=[table.value, fetch_all, hard_filter],
            max_instances=int(settings.MAX_CONCURENT_JOBS)
        )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")

@router.post(
    "/spawn_get_data_jobs/"
)
async def spawn__get_data():
    """Создать задачи для получения данных"""
    try:
        scheduler_service.instance.add_job(
            __spawn_get_data_jobs_job,
        )
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Возникла ошибка: {str(ex)}")
# @router.get(
#     "/currently_executing"  
# )
# async def get_currently_executing():
#     """Получить текущие выполняемые задачи"""
#     return scheduler_service.get_currently_executing_jobs

# @router.get(
#     "/{job_id}/basic_info", response_model=JobOut)
# async def get_job_basic_info(
#     job_id: str,
#     session=Depends(get_sync_session)
# ):
#     """Получить базовую информацию по задаче из базы"""
#     job = job_crud.get(session, job_id)
#     if not job:
#         raise JobNotFoundException(job_id)
#     return job

# @router.get("/{job_id}/extended_info", response_model=JobOutExtendedInfo)
# async def get_job_extended_info(
#     job_id: str,
#     session=Depends(get_sync_session)
# ):
#     """Получить полную информацию по задаче из базы"""
#     job = job_crud.get_job_extended_info(session, job_id)
#     if not job:
#         raise JobNotFoundException(job_id)
#     return job


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

# @router.post(
#     "/update_all", 
#     dependencies=[Depends(scheduler_service.update_all_job_check)], 
#     response_model=JobScheduledResponse
# )
# async def update_all_tables(
#     fetch_all: bool = False,
#     schedules: dict = Depends(schedules),
#     hard_filter: str = None
# ):
#     """Обновить все таблицы"""
#     try:
#         id = str(uuid.uuid4())
#         job = scheduler_service.add_job(
#             schedules=schedules,
#             func=update_all_wraper,
#             job_id=id,
#             job_name='update_all',
#             args=[fetch_all, id, hard_filter]
#         )
#         return job
#     except Exception as ex:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         detail=f"Возникла ошибка: {str(ex)}")
  
# @router.post(
#     "/update/{table}", 
#     dependencies=[Depends(scheduler_service.update_job_check)], 
#     response_model=JobScheduledResponse
# )
# async def update_table_job(
#     table: Table,
#     fetch_all: bool = False,
#     schedules: dict = Depends(schedules),
#     hard_filter: str = None
# ):
#     """Обновить указанную таблицу"""
#     try:
#         id = str(uuid.uuid4())
#         job = scheduler_service.add_job(
#             schedules=schedules,
#             func=update_wraper,
#             job_id=id,
#             job_name=f'update_{table}',
#             args=[table, id, fetch_all, hard_filter]
#         )
#         return job
#     except Exception as ex:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         detail=f"Возникла ошибка: {str(ex)}")

# @router.post(
#     "/test_coroutine", 
#     dependencies=[Depends(scheduler_service.test_job_check)],
#     response_model=JobScheduledResponse
# )
# async def test_for_coroutine(
#     schedules: dict = Depends(schedules),
# ):
#     try:
#         id = str(uuid.uuid4())
#         job = scheduler_service.add_job(
#             schedules=schedules,
#             func=test_job_main,
#             job_id=id,
#             job_name='test_job_main',
#             args=[id]
#         )
#         return job
#     except Exception as ex:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         detail=f"Возникла ошибка: {str(ex)}")

# @router.post(
#     "/clean_up_jobs",
#     response_model=JobScheduledResponse, 
#     dependencies=[Depends(scheduler_service.jobs_cleanup_check)]
# )
# async def clean_up_jobs(
#     schedules: dict = Depends(schedules),   
# ):
#     """Удалить застывшие задачи"""
#     try:
#         id = str(uuid.uuid4())
#         job = scheduler_service.add_job(
#             schedules=schedules,
#             func=jobs_clean_up,
#             job_id=id,
#             job_name='clean_up_jobs',
#         )
#         return job
#     except Exception as ex:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         detail=f"Возникла ошибка: {str(ex)}")