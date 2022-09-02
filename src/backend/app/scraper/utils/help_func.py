import datetime
import psycopg2
from typing import List, Any
import uuid
from apscheduler.job import Job as APSJob
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.util import undefined
import logging
import json
from sqlalchemy.orm import Session
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_not_exception_type
)
from tenacity.wait import wait_fixed

from scraper.config import settings
from scraper.models import Job as PersistanceJob
from db.session import async_session, sync_session

logger = logging.getLogger(__name__)

class JobHelper:
    """Сборник вспомогательных функций для задач"""
    @staticmethod
    def split_list(origin_list: List[Any], list_count: int):
        """Разделение списка на `list_count` кусков"""
        if len(origin_list) <= 0:
            raise ValueError("Исходный список пуст")
        if list_count <= 0:
            raise ValueError("Количество не должно быть равно 0")
        return list(JobHelper.__split_list(origin_list, list_count))

    @staticmethod
    def __split_list(origin_list: List[Any], list_count: int):
        k, m = divmod(len(origin_list), list_count)
        for i in range(list_count):
            yield origin_list[i*k+min(i, m):(i+1)*k+min(i+1, m)]

    @staticmethod
    def __range_builder(
        table_count: int
    ):
        limit = int(settings.TABLE_LIMIT)
        item = None
        range_list = []
        steps = table_count // limit
        for idx, i_item in enumerate(range(0, table_count, limit)):
            if idx == steps:
                range_list.append(f'{i_item}-{table_count}')
                continue
            if item != None:
                range_list.append(f'{item}-{i_item}')
                item = None
            else:
                item = i_item
        range_list.reverse()
        return range_list

    @staticmethod
    def make_range_list(
        table_count: int,
        list_count: int
    ):
        """Создает список списков последовательностей"""
        if table_count <= 0:
            raise ValueError("Общее кол-во таблицы <= 0")
        return list(JobHelper.__split_list(
            JobHelper.__range_builder(table_count), list_count
        ))

        
    @staticmethod
    async def create_child_jobs_async(
        parent_id: str,
        jobs_amount: int
    ):
        """Запись информации о задаче в базу данных"""
        async with async_session() as session:
            try:
                for _ in range(jobs_amount):
                    db_job = PersistanceJob(
                        id = str(uuid.uuid4()),
                        parent_job_id = parent_id
                    )
                    session.add(db_job)
                await session.commit()
            except Exception as ex:
                logger.error('При сохранении информации о задачи ' +
                    f'возникла ошибка {ex}')

    @staticmethod
    def create_child_jobs(
        parent_id: str,
        jobs_amount: int
    ):
        """Запись информации о задаче в базу данных"""
        try:
            session = sync_session()
            for _ in range(jobs_amount):
                # new_job = JobCreate(
                #     id=str(uuid.uuid4()),
                #     parent_job_id = parent_id
                # )
                # job_crud.create(session=session, obj_in=new_job)
                db_job = PersistanceJob(
                    id = str(uuid.uuid4()),
                    parent_job_id = parent_id
                )
                session.add(db_job)                
            session.commit()                
        except Exception as ex:
            logger.error('При сохранении информации о задачи ' +
                f'возникла ошибка {ex}')
        finally:
            session.close()


    @staticmethod
    async def update_job_async(
        id: str
    ):
        "Обновление информации о задаче"
        async with async_session() as session:
            try:
                db_job: PersistanceJob = \
                    await session.get(PersistanceJob, db_job.id)
                if db_job and db_job.is_all_childs_completed():
                    db_job.set_complete_date()
                await session.commit()
            except Exception as ex:
                logger.error('При обновлении задачи ' +
                f'возникла ошибка {ex}')

    @staticmethod
    def get_prepared_job(
        parent_id: str,
        session: Session,
        scheduler: BaseScheduler = None
    ):
        """Получить дочернюю задачу, чьё выполнение ещё не началось"""
        db_job: PersistanceJob = session.query(PersistanceJob).filter_by(
            parent_job_id = parent_id, time_started = None
        ).first()
        return db_job

    @retry(
        stop=stop_after_attempt(int(settings.CLIENT_RETRY_ATTEMPTS)),
        wait=wait_fixed(2),
        retry=retry_if_not_exception_type(psycopg2.errors.UniqueViolation)
    )
    def try_to_add_prepared_job(
        parent_id: str,
        session: Session,
        scheduler: BaseScheduler,
        func,
        trigger=None,
        args=None,
        kwargs=None,
        name=None,
        misfire_grace_time=undefined,
        coalesce=undefined,
        max_instances=undefined,
        next_run_time=undefined,
        jobstore='default',
        executor='default',
        replace_existing=False,
        **trigger_args: Any
    ):
        """Попытка добавить задачу в шедулер"""
        prepared_job = JobHelper.get_prepared_job(parent_id, session)
        if not prepared_job:
            raise ValueError('Не удается получить дочернюю задачу')
        scheduler.add_job(
            func=func,
            trigger=trigger,
            args=args,
            kwargs=kwargs,
            id=prepared_job.id,
            name=name,
            misfire_grace_time=misfire_grace_time,
            coalesce=coalesce,
            max_instances=max_instances,
            next_run_time=next_run_time,
            jobstore=jobstore,
            executor=executor,
            replace_existing=replace_existing,
            **trigger_args
        )



class SerializerHelper:
    """Сборник вспомогательных функций для сериализации"""
    @staticmethod
    def convert_datetime_to_iso_8601(dt: datetime) -> str:
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    @staticmethod
    def convert_timedelta_to_seconds(td: datetime.timedelta) -> int:
        return td.seconds