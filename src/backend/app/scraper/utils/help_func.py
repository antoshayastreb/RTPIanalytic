import datetime
from typing import List, Any
from apscheduler.job import Job as APSJob
import logging
import json
from apscheduler.schedulers.base import BaseScheduler
from sqlalchemy import event

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
        #list_len = len(origin_list)
        #assert list_len > 0
        #sub_list_len = len(list) // list_len
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
    async def create_job_async(
        jobs: List[APSJob],
        parent_id = None
    ):
        """Запись информации о задаче в базу данных"""
        async with async_session() as session:
            try:
                for job in jobs:
                    db_job = PersistanceJob(
                        id = job.id,
                        name = job.name,
                        args = [
                            str(arg) for arg in job.args
                        ],
                        time_started = datetime.datetime.now(),
                        kwargs = json.dumps(job.kwargs),
                        parent_job_id = parent_id
                    )
                    session.add(db_job)
                await session.commit()
            except Exception as ex:
                logger.error('При сохранении информации о задачи ' +
                    f'возникла ошибка {ex}')

    @staticmethod
    def create_job(
        jobs: List[APSJob],
        parent_id = None
    ):
        """Запись информации о задаче в базу данных"""
        try:
            session = sync_session()
            for job in jobs:
                db_job = PersistanceJob(
                    id = job.id,
                    name = job.name,
                    args = [
                        str(arg) for arg in job.args
                    ],
                    time_started = datetime.datetime.now(),
                    kwargs = json.dumps(job.kwargs),
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
    def update_job(
        id: str
    ):
        "Обновление информации о задаче"
        session = sync_session()
        try:
            db_job: PersistanceJob = \
                session.get(PersistanceJob, id)
            if db_job:
                db_job.set_complete_date()
            session.commit()
        except Exception as ex:
            logger.error('При обновлении задачи ' +
                f'возникла ошибка {ex}')
        finally:
            session.close()