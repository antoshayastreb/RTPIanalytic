import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.events import JobExecutionEvent
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_ADDED
)
from random import randint

from scraper.utils.exeptions.scheduler import SchedulerStopedException
from scraper.config import settings
from scraper.utils.help_func import JobHelper

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.SQLALCHEMY_DATABASE_URI)
}

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

job_defaults = {
    'coalesce': settings.COALESCE.lower() == 'true',
    'max_instances': 20
}

def on_job_completed(event: JobExecutionEvent):
    JobHelper.complete_job(event.job_id, event.exception)

# def on_job_error(event: JobExecutionEvent):
#     JobHelper.complete_job(event.job_id, event.exception)

def on_job_added(event: JobExecutionEvent):
    scheduler = scheduler_service.get_scheduler()
    job = scheduler.get_job(event.job_id)
    JobHelper.start_job(job)


class SchedulerService(object):
    def __init__(self) -> None:
        self.number = randint(0, 10)
        self.scheduler: BaseScheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            # job_defaults=job_defaults, 
            timezone='Europe/Moscow'
        )
        self.scheduler.add_listener(on_job_completed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.add_listener(on_job_added, EVENT_JOB_ADDED)
        # self.scheduler.configure(
        #     #Конфиг APSchedler
        #     #https://apscheduler.readthedocs.io/en/stable/userguide.html
        #     {
        #         'apscheduler.jobstores.default': {
        #             'type': 'sqlalchemy',
        #             'url': settings.SQLALCHEMY_DATABASE_URI
        #         },
        #         'apscheduler.executors.default': {
        #             'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        #             'max_workers': '10'
        #         },
        #         # 'apscheduler.executors.processpool': {
        #         #     'type': 'processpool',
        #         #     'max_workers': '2'
        #         # },
        #         'apscheduler.job_defaults.coalesce': settings.COALESCE,
        #         'apscheduler.job_defaults.max_instances': settings.MAX_INSTANCES,
        #         'apscheduler.timezone': 'Europe/Moscow',
        #     }
        #)
    
    def __str__(self) -> str:
        return "APSchedulerService"
    
    def get_scheduler(self) -> BaseScheduler:
        return self.scheduler
    
    def scheduler_running_check(self) -> None:
        if not self.scheduler.running:
            raise SchedulerStopedException

scheduler_service = SchedulerService()

# def get_scheduler(request: Request) -> AsyncIOScheduler:
#     return request.app.state.scheduler_service