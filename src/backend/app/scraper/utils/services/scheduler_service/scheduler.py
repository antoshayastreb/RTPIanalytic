from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi import Request
from random import randint

from scraper.config import settings

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.SQLALCHEMY_DATABASE_URI)
}

executors={
    "default": AsyncIOExecutor(), 
    "cron": ThreadPoolExecutor()
},

job_defaults = {
    'coalesce': settings.COALESCE.lower() == 'true',
    'max_instances': int(settings.MAX_INSTANCES)
}


class SchedulerService(object):
    def __init__(self) -> None:
        self.number = randint(0, 10)
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults=job_defaults, 
            timezone='Europe/Moscow'
        )
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
    
    def get_scheduler(self) -> AsyncIOScheduler:
        return self.scheduler

scheduler_service = SchedulerService()

# def get_scheduler(request: Request) -> AsyncIOScheduler:
#     return request.app.state.scheduler_service