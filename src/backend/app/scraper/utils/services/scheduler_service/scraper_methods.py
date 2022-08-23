import asyncio
import datetime
from operator import rshift
import uuid
from dateutil import parser
from aiohttp import ClientTimeout
import logging
import copy
from yarl import URL
from typing import Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import random
from sqlalchemy.dialects.postgresql import insert
import asyncpg
from threading import current_thread

from ...help_func import JobHelper
from scraper.config import settings
from scraper.utils.services.scheduler_service import scheduler_service
from .session import ScraperSession
from scraper.db.base_class import Base
from scraper.models import (
    RtpiPrice,
    RtpiStoreId,
    RtpiPricePage,
    RtpiProductName
)
from scraper.db.session import async_session, sync_session

tables = {
    'rtpi_price': RtpiPrice,
    'rtpi_store_id': RtpiStoreId,
    'rtpi_price_page': RtpiPricePage,
    'rtpi_product_name': RtpiProductName
}

date_attributes = [
    'moment',
    'date_last_crawl',
    'date_observe',
    'date_last_in_stock',
    'date_add'
]

#Таймаут для метода получения кол-ва строк в таблице
get_count_timeout = ClientTimeout(total=int(settings.CLIENT_TIMEOUT_GET_COUNT))

#Таймат для метода получения контента
get_content_timeout = ClientTimeout(total=int(settings.CLIENT_TIMEOUT_GET_CONTENT))

logger = logging.getLogger(__name__)

class Updater:
    def __init__(self, table_name: str, limit: str = None) -> None:
        self.table_name = table_name
        self.limit = int(limit) if limit \
            else int(copy.copy(settings.TABLE_LIMIT))

    @staticmethod
    def request_builder(table_name: str, filter: str = None) -> URL:
        """Конструктор запроса"""
        return URL(f'/{table_name}?{filter}') if filter \
            else URL(f'/{table_name}')

    @staticmethod
    async def get_table_count(
        table_name: str,
        filter: str = None,
        ) -> int:
        """
        Получить кол-во записей из `table_name`

        `table_name` - наименование таблицы

        `filter` - фильтр запроса

        `scheduler` - шедулер
        """
        try:
            print(f'Обновление {table_name} {current_thread().getName()}')
            url= Updater.request_builder(table_name, filter)
            global count
            async with ScraperSession(timeout=get_count_timeout) as client:
                return await client.get_count(
                    url= url
                )
        except Exception as e:
            logger.error(f"Ошибка при получении кол-ва из таблицы {e}")

    async def get_content(
        self,  
        ranges: List[str],
        delay: int = 0
    ) -> None:
        """Основной метод получения данных с API ресурса"""
        range = ranges.pop()
        print(f'{range} для {self.table_name} {current_thread().getName()}')
        header = {
            'Range' : range
        }
        try:
            global content
            async with ScraperSession(timeout=get_content_timeout) as client:
                content = await client.get_json(
                    headers=header,
                    url=self.url
                )
            if content:
                await self.asyncpg_insert(content)
                #await self.write_to_base(content)
                if len(ranges) > 0:
                    await asyncio.sleep(delay)
                    scheduler = scheduler_service.get_scheduler()
                    scheduler.add_job(
                        self.get_content_wraper,
                        name=f'{self.table_name} {ranges[-1]}',
                        misfire_grace_time=None,
                        args=[ranges, 5]
                    )
        except Exception as ex:
            logger.error(f"Произошла ошибка при получении данных для таблицы {self.table_name} \
                в диапазоне {range}: {ex}")

    def get_stmt(self, content: Any):
        #model = tables[self.table_name]
        if 'rtpi_store_id' == self.table_name:
            stmt = insert(RtpiStoreId).values(content)
            return stmt.on_conflict_do_update(
                constraint='rtpistoreid_store_name_key',
                set_={
                    "store_name": stmt.excluded.store_name
                }
            )
        if 'rtpi_product_name' == self.table_name:
            stmt = insert(RtpiProductName).values(content)
            return stmt.on_conflict_do_update(
                constraint='web_price_id_moment_unique',
                set_={
                    "product_name": stmt.excluded.product_name,
                    "contributor_id": stmt.excluded.contributor_id
                }
            )
        if 'rtpi_price_page' == self.table_name:
            stmt = insert(RtpiPricePage).values(content)
            return stmt.on_conflict_do_update(
                constraint='web_price_id_unique',
                set_={
                    "price_name": stmt.excluded.price_name,
                    "price_url": stmt.excluded.price_url,
                    "date_add": stmt.excluded.date_add,
                    "date_last_in_stock": stmt.excluded.date_last_in_stock,
                    "rosstat_id": stmt.excluded.rosstat_id,
                    "contributor_id": stmt.excluded.contributor_id,
                    "store_id": stmt.excluded.store_id,
                    "date_last_crawl": stmt.excluded.date_last_crawl,
                    "city_code": stmt.excluded.city_code
                }
            )
        if 'rtpi_price' == self.table_name:
            stmt = insert(RtpiPrice).values(content)
            return stmt.on_conflict_do_update(
                constraint='web_price_id_date_observe_unique',
                set_={
                    "stock_status": stmt.excluded.stock_status,
                    "current_price": stmt.excluded.current_price,
                    "crosssed_price": stmt.excluded.crosssed_price,
                    "contributor_id": stmt.excluded.contributor_id
                }
            )

    async def asyncpg_insert(self, content: Any):
        """Базированный гигачадовый bulk upsert через asyncpg"""
        values: list[tuple] = []
        if isinstance(content[0], dict):
            values = [
                tuple(item.values()) \
                    for item in content
            ]
        else:
            values = content
        conn: asyncpg.connection.Connection \
            = await asyncpg.connect(dsn=settings.SQLALCHEMY_DATABASE_URI)
        try:
            stmt = Updater.make_sql(self.table_name)
            await conn.executemany(
                stmt,
                values
            )
        except Exception as ex:
            logger.error(f"Ошибка при комите: {ex}")
        finally:
            await conn.close()

    @staticmethod
    def make_sql(table_name: str):
        if table_name == "rtpi_store_id":
            sql = '''INSERT INTO rtpistoreid (store_id, store_name) \
            VALUES ($1,$2) \
            ON CONFLICT \
            DO NOTHING; '''
            return sql
        if table_name == "rtpi_price_page":
            sql = '''INSERT INTO rtpipricepage (web_price_id, price_name, price_url, date_add, date_last_crawl, date_last_in_stock, rosstat_id, contributor_id, store_id, city_code) \
            VALUES ($1,$2,$3,to_timestamp($4, 'YYYY-MM-DD T HH24:MI:SS:MS'),to_timestamp($5, 'YYYY-MM-DD T HH24:MI:SS:MS'),to_timestamp($6, 'YYYY-MM-DD T HH24:MI:SS:MS'),$7,$8,$9,$10) \
            ON CONFLICT ON CONSTRAINT web_price_id_unique\
            DO UPDATE \
            SET (price_name, price_url, date_add, date_last_crawl, date_last_in_stock, rosstat_id, contributor_id, store_id, city_code) \
            = (excluded.price_name, excluded.price_url, excluded.date_add, excluded.date_last_crawl, excluded.date_last_in_stock, excluded.rosstat_id, excluded.contributor_id, excluded.store_id, excluded.city_code); '''
            return sql
        if table_name == "rtpi_product_name":
            sql = '''INSERT INTO rtpiproductname (web_price_id, product_name, contributor_id, moment) \
            VALUES ($1,$2,$3,to_timestamp($4, 'YYYY-MM-DD T HH24:MI:SS:MS')) \
            ON CONFLICT \
            DO NOTHING;'''
            return sql   
        if table_name == "rtpi_price":
            sql = '''INSERT INTO rtpiprice (web_price_id, date_observe, stock_status, current_price, crosssed_price, contributor_id) \
            VALUES ($1,to_timestamp($2, 'YYYY-MM-DD T HH24:MI:SS:MS'),$3,$4,$5,$6) \
            ON CONFLICT ON CONSTRAINT web_price_id_date_observe_unique \
            DO UPDATE \
            SET (stock_status, current_price, crosssed_price, contributor_id) \
            = (excluded.stock_status, excluded.current_price, excluded.crosssed_price, excluded.contributor_id);'''
            return sql

    async def write_to_base(self, content: Any):
        """Поридж куколдовый сойджак орм метод записи"""
        new_objects = [
            self.fit_to_model(json_object)
                for  json_object in content
        ]
        async with async_session() as session:
            session.add_all(new_objects)
            try:
                await session.commit()
            except Exception as ex:
                logger.error(f"Ошибка при комите: {ex}")
                await session.rollback()
        
    def fit_to_model(self, json_object: str):
        """Перевести json в модель"""
        model = tables[self.table_name]
        obj = model(**json_object)
        for atr in date_attributes:
            if hasattr(obj, atr):
                obj_atr = getattr(obj, atr)
                if isinstance(obj_atr, str):
                    setattr(obj, atr, parser.parse(obj_atr))
        return obj


    @staticmethod
    async def get_exist_object(session: AsyncSession, obj: Any):
        """Получить существующий объект или None"""
        if isinstance(obj, RtpiStoreId):
            return await session.scalar(
                select(RtpiStoreId)
                .where(RtpiStoreId.store_name == obj.store_name)
            )
        if isinstance(obj, RtpiProductName):
            return await session.scalar(
                select(RtpiProductName)
                .where(RtpiProductName.web_price_id == obj.web_price_id,
                RtpiProductName.moment == obj.moment)
            )
        if isinstance(obj, RtpiPrice):
            return await session.scalar(
                select(RtpiPrice)
                .where(RtpiPrice.web_price_id == obj.web_price_id,
                RtpiPrice.date_observe == obj.date_observe)
            )
        if isinstance(obj, RtpiPricePage):
            return await session.scalar(
                select(RtpiPricePage)
                .where(RtpiPricePage.web_price_id == obj.web_price_id)
            )

    @staticmethod
    def update_data(obj: Any, new_obj: Any):
        """Перенос изменений из старого объекта в новый"""
        new_obj_dict = vars(new_obj)
        update_data = {x: new_obj_dict[x] \
        for x in new_obj_dict if x != 'id' \
        and x != '_sa_instance_state'}
        for key, value in update_data.items():
            setattr(obj, key, value)

    def count_iterat_count(self, table_count: int) -> 'tuple[int, int]':
        """Расчет итераций, для дальнейшего распределения"""
        iterat_count = table_count // self.limit
        while iterat_count == 0:
            self.limit -= 100
            if self.limit == 0:
                iterat_count = table_count
                break
            else:
                iterat_count = table_count // self.limit

        addit_count = table_count - self.limit * iterat_count

        return iterat_count, addit_count

    def produce_jobs(self, table_count: int):
        """Создание задач"""
        scheduler = scheduler_service.get_scheduler()
        max = int(settings.MAX_CONCURENT_JOBS)
        range_list = JobHelper.make_range_list(table_count, max)
        for ranges in range_list:
            if len(ranges) > 0:
                scheduler.add_job(
                    self.get_content_wraper,
                    name=f'{self.table_name} {ranges[0]}',
                    misfire_grace_time=None,
                    args=[ranges, 0]
                )
    def get_content_wraper(self, *args):
        asyncio.run(self.get_content(*args))

async def update_table(table_name: str):
    try:
        updater = Updater(table_name)
        count = await updater.get_table_count(table_name)
        assert count != None
        updater.url = Updater.request_builder(table_name)
        updater.produce_jobs(count)
    except AssertionError as ex:
        logger.error(f"При обновлении таблицы {table_name} не удалось получить кол-во строк")
    except Exception as ex:
        logger.error(f"При обновлении таблицы {table_name} произошла ошибка {ex}")

async def test_coroutine_job(
    args_list: list = None,
    delay: int = 0,
    parent_id: str = None
):
    """Тестовый метод, без обращений к апи и к базе"""
    try:
        session = sync_session()
        start_time = datetime.datetime.now()
        wait_time = random.randint(0, 10)
        await asyncio.sleep(wait_time)
        end_time = datetime.datetime.now()
        print(f"Прождали {end_time-start_time} сек, начали {start_time}, закончили {end_time}")
        if len(args_list) > 0:
            await asyncio.sleep(delay)
            args_list.pop()
            scheduler = scheduler_service.get_scheduler()
            id = JobHelper.get_prepared_job(parent_id, session, scheduler)
            scheduler.add_job(
                test_job_wrapper,
                id=id,
                misfire_grace_time=None,
                args=[args_list, delay, parent_id]
            )
    except Exception as ex:
        logger.error('В тестовой задаче произошла ошибка ' +
        f'{ex}')
    finally:
        session.close()

def update_wraper(*args):
    asyncio.run(update_table(*args))

def test_job_main(
    parent_id: str
):
    try:
        session = sync_session()
        main_args_list = [
            i for i in range (0, 100)
        ]
        max = int(settings.MAX_CONCURENT_JOBS)
        JobHelper.create_child_jobs(parent_id, len(main_args_list))
        splited_list = JobHelper.split_list(main_args_list, max)
        scheduler = scheduler_service.get_scheduler()
        db_parent_job = JobHelper.get_job_by_id(parent_id, session)
        if not db_parent_job:
            raise ValueError('В базе отсутсвует основная задача, ' + 
            'невозможно получить дочерние')
        for idx, inner_list in enumerate(splited_list):
            child_job_id = db_parent_job.child_jobs[idx].id
            scheduler.add_job(
                test_job_wrapper,
                id = child_job_id,
                args=[inner_list, 0, parent_id],
                misfire_grace_time=None
            )
    except Exception as ex:
        logger.error('Произошла ошибка в главной тестовой задаче ' +
        f'{ex}')
    finally:
        session.close()
    

def test_job_wrapper(
        args_list: list = None, 
        delay: int = 0, 
        parent_id: str = None
    ):
        asyncio.run(test_coroutine_job(args_list, delay, parent_id))

