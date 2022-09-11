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
    EVENT_JOB_SUBMITTED,
    EVENT_JOB_ADDED,
    EVENT_SCHEDULER_START,
    EVENT_SCHEDULER_SHUTDOWN
)
from random import randint
from datetime import datetime
import json
import logging

from scraper.db.session import sync_session
from scraper.utils.exeptions.scheduler import SchedulerStopedException, MaxJobInstancesReached
from scraper.config import settings
from scraper.schemas.job import JobScheduledResponse
from scraper.models import (
    Job as PersistanceJob,
    Table
)

logger = logging.getLogger(__name__)

job_instance_amount = {
    'test_job_main': int(settings.TEST_MAIN_MAX_INSTANCES),
    'update_all': int(settings.UPDATE_MAX_INSTANCES),
    'update_rtpi_price': int(settings.UPDATE_MAX_INSTANCES),
    'update_rtpi_price_page': int(settings.UPDATE_MAX_INSTANCES),
    'update_rtpi_product_name': int(settings.UPDATE_MAX_INSTANCES),
    'update_rtpi_store_id': int(settings.UPDATE_MAX_INSTANCES),
    'clean_up_jobs': int(settings.CLEANUP_MAX_INSTANCES)
}

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.SQLALCHEMY_DATABASE_URI)
}

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

job_defaults = {
    'coalesce': settings.COALESCE.lower() == 'true',
    'max_instances': 10
}

def on_scheduler_start(event: SchedulerEvent):
    pass

def on_scheduler_shutdown(event: SchedulerEvent):
    #Очистка текущих запущенных задач на выключении шедулера
    scheduler_service.currently_executing = []

def on_job_completed(event: JobExecutionEvent):
    scheduler_service._complete_job(event.job_id,
    event.exception)

# def on_job_error(event: JobExecutionEvent):
#     JobHelper.complete_job(event.job_id, event.exception)

def on_job_added(event: JobExecutionEvent):
    scheduler = scheduler_service.get_scheduler()
    job = scheduler.get_job(event.job_id)
    scheduler_service._create_job(job)

def on_job_submitted(event: JobExecutionEvent):
    # scheduler = scheduler_service.get_scheduler()
    # job = scheduler.get_job(event.job_id)
    scheduler_service._start_job(event.job_id)

class SchedulerService(object):
    def __init__(self) -> None:
        self.currently_executing: List[str] = []
        self.number = randint(0, 10)
        self.scheduler: BaseScheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults, 
            timezone='Europe/Moscow'
        )
        self.scheduler.add_listener(on_job_completed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.add_listener(on_job_added, EVENT_JOB_ADDED)
        self.scheduler.add_listener(on_job_submitted, EVENT_JOB_SUBMITTED)
        self.scheduler.add_listener(on_scheduler_start, EVENT_SCHEDULER_START)
        self.scheduler.add_listener(on_scheduler_shutdown, EVENT_SCHEDULER_SHUTDOWN)
    
    def __str__(self) -> str:
        return "APSchedulerService"
    
    def get_scheduler(self) -> BaseScheduler:
        return self.scheduler
    
    def get_currently_executing_jobs(self):
        return self.currently_executing

    def _add_to_currently_executing(self, job: PersistanceJob) -> None:
        #self.__job_already_running_check(job.name)
        self.currently_executing.append(job.name)
    
    def _create_job(
        self,
        job: APSJob
    ):
        """Создание задачи без даты старта"""
        try:
            session = sync_session()
            db_job: PersistanceJob = session.get(PersistanceJob, job.id)
            if not db_job:
                db_job = PersistanceJob(
                    id = job.id
                )
            db_job.name = job.name
            db_job.args = [
                str(arg) for arg in job.args
            ]
            db_job.kwargs = json.dumps(job.kwargs)
            session.add(db_job)
            session.commit()            
        except Exception as ex:
            logger.error('При сохранении информации о задаче ' +
                f'возникла ошибка {ex}')
        finally:
            session.close()

    def _start_job(
        self,
        job_id: str,
        #job: APSJob,
    ):
        """Обновление информации на старте"""
        try:
            session = sync_session()
            db_job: PersistanceJob = session.get(PersistanceJob, job_id)
            if not db_job:
                raise ValueError(f'Задача с {job_id} не найдена')
            db_job.time_started = datetime.now()
            session.add(db_job)
            session.commit()
            self._add_to_currently_executing(db_job)               
        except Exception as ex:
            logger.error('При сохранении информации о задаче ' +
                f'возникла ошибка {ex}')
        finally:
            session.close()

    def _complete_job(
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
            session.refresh(db_job)
            self._remove_from_currently_executing(db_job)
        except Exception as ex:
            logger.error('При обновлении задачи ' +
                f'возникла ошибка {ex}')
        finally:
            session.close()

    def _remove_from_currently_executing(self, job: PersistanceJob) -> None:
        if job.name in self.currently_executing:
            self.currently_executing.remove(job.name)

    def scheduler_running_check(self) -> None:
        if not self.scheduler.running:
            raise SchedulerStopedException

    def test_job_check(self) -> None:
        self.__job_already_running_check('test_job_main')

    def update_all_job_check(self) -> None:
        self.__job_already_running_check('update_all')

    def update_job_check(self, table: Table) -> None:
        self.__job_already_running_check(f"update_{table}")

    def jobs_cleanup_check(self) -> None:
        self.__job_already_running_check('clean_up_jobs')

    def __job_already_running_check(self, job_name: str) -> None:
        if job_name not in job_instance_amount.keys():
            return
        max_for_job = job_instance_amount[job_name]
        already_in = self.currently_executing.count(job_name)
        if already_in >= max_for_job:
            raise MaxJobInstancesReached(job_name, already_in, max_for_job)
    
    def _get_trigger(
        self,
        schedules: 'dict[str, Any]'
    ):
        """Получить тип триггера и его аргументы."""
        if schedules['interval_schedule']:
            return 'interval', vars(schedules['interval_schedule'])
        if schedules['date_schedule']:
            return 'date', vars(schedules['date_schedule'])
        if schedules['cron_schedule']:
            return 'cron', vars(schedules['cron_schedule'])
        return None, None

    def add_job(
        self,
        schedules: 'dict[str, Any]',
        func: Any,
        job_id: Any = None,
        job_name: str = None,
        args: 'list[Any]' = [] 
    ):
        """
        Обертка метода `scheduler.add_job`.

        Поддерживает триггеры.
        """
        trigger, trigger_args = self._get_trigger(schedules)
        if trigger and trigger_args:
            job: APSJob = self.scheduler.add_job(
                func=func,
                id=job_id,
                trigger=trigger,
                **trigger_args,
                misfire_grace_time=None,
                name=job_name,
                args=args
            )
        else:
            job: APSJob = self.scheduler.add_job(
                func=func,
                id=job_id,
                misfire_grace_time=None,
                name=job_name,
                args=args                
            )
        return JobScheduledResponse (
            id=job.id,
            name=job.name,
            next_run_time=job.next_run_time
        )

scheduler_service = SchedulerService()