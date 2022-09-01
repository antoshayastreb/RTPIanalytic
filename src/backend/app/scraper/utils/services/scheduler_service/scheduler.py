from typing import List, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.events import JobExecutionEvent, SchedulerEvent
from apscheduler.job import Job as APSJob
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_ADDED,
    EVENT_SCHEDULER_START,
    EVENT_SCHEDULER_SHUTDOWN
)
from random import randint
from datetime import datetime
import json
import logging

from scraper.db.session import sync_session
from scraper.utils.exeptions.scheduler import SchedulerStopedException
from scraper.config import settings
from scraper.crud.jobs import job_crud
from scraper.models import Job as PersistanceJob


logger = logging.getLogger(__name__)

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.SQLALCHEMY_DATABASE_URI)
}

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

job_defaults = {
    'coalesce': settings.COALESCE.lower() == 'true'
    #'max_instances': 1
}

job_max_amount = {
    
}

def on_scheduler_start(event: SchedulerEvent):
    pass

def on_scheduler_shutdown(event: SchedulerEvent):
    pass

def on_job_completed(event: JobExecutionEvent):
    scheduler_service.complete_job(event.job_id,
    event.exception)

# def on_job_error(event: JobExecutionEvent):
#     JobHelper.complete_job(event.job_id, event.exception)

def on_job_added(event: JobExecutionEvent):
    scheduler = scheduler_service.get_scheduler()
    job = scheduler.get_job(event.job_id)
    scheduler_service.start_job(job)

class SchedulerService(object):
    def __init__(self) -> None:
        #self.currently_executing: List[str] = []
        self.number = randint(0, 10)
        self.scheduler: BaseScheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults, 
            timezone='Europe/Moscow'
        )
        self.scheduler.add_listener(on_job_completed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.add_listener(on_job_added, EVENT_JOB_ADDED)
        self.scheduler.add_listener(on_scheduler_start, EVENT_SCHEDULER_START)
        self.scheduler.add_listener(on_scheduler_shutdown, EVENT_SCHEDULER_SHUTDOWN)
    
    def __str__(self) -> str:
        return "APSchedulerService"
    
    def get_scheduler(self) -> BaseScheduler:
        return self.scheduler
    
    def get_currently_executing_jobs(self) -> None:
        #return self.currently_executing
        pass

    def add_to_currently_executing(self, job: PersistanceJob) -> None:
        #self.currently_executing.append(job.func)
        pass
    
    def start_job(
        self,
        job: APSJob,
    ):
        """Обновление информации на старте"""
        try:
            session = sync_session()
            db_job: PersistanceJob = session.get(PersistanceJob, job.id)
            if not db_job:
                db_job = PersistanceJob(id = job.id)
            db_job.func = str(job.func_ref)
            db_job.name = job.name
            db_job.args = [
                        str(arg) for arg in job.args
            ]
            db_job.time_started = datetime.now()
            db_job.kwargs = json.dumps(job.kwargs)
            #db_job.parent_job_id = parent_id
            session.add(db_job)
            session.commit()
            #self.add_to_currently_executing(db_job)               
        except Exception as ex:
            logger.error('При сохранении информации о задачи ' +
                f'возникла ошибка {ex}')
        finally:
            session.close()

    def complete_job(
        self,
        id: str,
        exception: Any = None
    ):
        "Завершение задачи"
        try:
            session = sync_session()
            db_job: PersistanceJob = \
                session.get(PersistanceJob, id)
            if db_job:
                db_job.set_complete_date()
                if exception:
                    db_job.exception_text = str(exception)
            session.commit()
            #scheduler_service.remove_from_currently_executing(db_job)
        except Exception as ex:
            logger.error('При обновлении задачи ' +
                f'возникла ошибка {ex}')
        finally:
            session.close()

    def remove_from_currently_executing(self, db_job: PersistanceJob) -> None:
        # if db_job.func in self.currently_executing:
        #     self.currently_executing.remove(db_job.func)
        #     if db_job.parent_job and db_job.parent_job.time_completed:
        #         self.remove_from_currently_executing(db_job.parent_job)
        pass

    def scheduler_running_check(self) -> None:
        if not self.scheduler.running:
            raise SchedulerStopedException

    def job_already_running_check(self, job) -> None:
        pass

scheduler_service = SchedulerService()

# def get_scheduler(request: Request) -> AsyncIOScheduler:
#     return request.app.state.scheduler_service