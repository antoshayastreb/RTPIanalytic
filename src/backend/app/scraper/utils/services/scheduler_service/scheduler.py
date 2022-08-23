import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.events import JobEvent
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_ADDED
)
from fastapi import Request
from random import randint

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
    #'max_instances': int(settings.MAX_CONCURENT_JOBS)
}

def on_job_completed(event: JobEvent):
    JobHelper.complete_job(event.job_id)

def on_job_added(event: JobEvent):
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

scheduler_service = SchedulerService()

# def get_scheduler(request: Request) -> AsyncIOScheduler:
#     return request.app.state.scheduler_service