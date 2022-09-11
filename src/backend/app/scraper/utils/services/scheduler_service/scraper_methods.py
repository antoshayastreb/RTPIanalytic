import time
import asyncio
import datetime
from enum import Enum
from dateutil import parser
from aiohttp import ClientTimeout
import logging
import copy
from yarl import URL
from typing import Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import random
from sqlalchemy.dialects.postgresql import insert
import asyncpg
from threading import current_thread

from ...help_func import JobHelper
from scraper.config import settings
from scraper.utils.services.scheduler_service import scheduler_service
from .session import ScraperSession
from scraper.models import (
    RtpiPrice,
    RtpiStoreId,
    RtpiPricePage,
    RtpiProductName,
    Job as PersistanceJob
)
from scraper.crud.jobs import job_crud
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

class Ordering(Enum):
    ASCENDING = '.asc'
    DESCENDING = '.desc'

#Таймаут для метода получения кол-ва строк в таблице
get_count_timeout = ClientTimeout(total=int(settings.CLIENT_TIMEOUT_GET_COUNT))

#Таймат для метода получения контента
get_content_timeout = ClientTimeout(total=int(settings.CLIENT_TIMEOUT_GET_CONTENT))

logger = logging.getLogger(__name__)

class Updater:
    def __init__(self, table_name: str, nu: bool = False, limit: str = None) -> None:
        #Запись в 'неуникальные' таблицы
        self.nu = nu
        self.table_name = table_name
        self.table_name_disp = f'nu_{table_name}' if nu \
            else table_name
        self.limit = int(limit) if limit \
            else int(copy.copy(settings.TABLE_LIMIT))

    @staticmethod
    def request_builder(table_name: str, filter: str = None) -> URL:
        """Конструктор запроса"""
        return URL(f'/{table_name}?{filter}') if filter \
            else URL(f'/{table_name}')
    
    def make_update_filter(self, value: str) -> 'str | None':
        """Создать фильтр, с учётом последней даты"""
        if value:
            if self.table_name == 'rtpi_price_page':
                return f'date_last_in_stock=gte.{value}'
            if self.table_name == 'rtpi_product_name':
                return f'moment=gte.{value}'
            if self.table_name == 'rtpi_price':
                return f'date_observe=gte.{value}'
        return None

    def get_order_filter(self, 
        value: str = None, 
        order: Ordering = Ordering.ASCENDING) -> 'str | None':
        """
        Получить фильтр сортировки.

        Фильтр строится на основе наименования таблицы, но также
        можно использовать `value` для задания поля фильтрации.

        `order` используется для задания фильтрации, по умолчанию `asc`.
        """
        if value:
            return f'order={value}{order.value}'
        if self.table_name in [
            'rtpi_price',
            'rtpi_price_page',
            'rtpi_product_name'
            ]:
            return f'order=web_price_id{order.value}'
        return None
        

    def get_last_date(self) -> 'str | None':
        """Получить последнюю дату из таблицы"""
        try:
            session = sync_session()
            date = None
            if self.table_name == 'rtpi_price_page':
                date = session.query(RtpiPricePage.date_last_in_stock). \
                    order_by(desc(RtpiPricePage.date_last_in_stock)). \
                        limit(1).first() 
            if self.table_name == 'rtpi_product_name':
                date = session.query(RtpiProductName.moment). \
                    order_by(desc(RtpiProductName.moment)). \
                        limit(1).first() 
            if self.table_name == 'rtpi_price':
                date = session.query(RtpiPrice.date_observe). \
                    order_by(desc(RtpiPrice.date_observe)). \
                        limit(1).first()                              
            return date[0].strftime('%Y-%m-%dT%H:%M:%S') if date else date
        except Exception as ex:
            raise ex
        finally:
            session.close()

    async def get_last_date_async(self) -> 'str | None':
        """Получить последнюю дату из таблицы"""
        async with async_session() as session:
            stmt = None
            if self.table_name == 'rtpi_price_page':
                stmt = select(RtpiPricePage.date_last_in_stock). \
                    order_by(desc(RtpiPricePage.date_last_in_stock)). \
                        limit(1)
            if self.table_name == 'rtpi_product_name':
                stmt = select(RtpiProductName.moment). \
                    order_by(desc(RtpiProductName.moment)). \
                        limit(1)
            if self.table_name == 'rtpi_price':
                stmt = select(RtpiPrice.date_observe). \
                    order_by(desc(RtpiPrice.date_observe)). \
                        limit(1)
            if stmt != None:
                return (await session.scalars(stmt)).first().strftime('%Y-%m-%dT%H:%M:%S')
            return None

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
        ranges: 'list[int]',
        parent_id: str,
        #delay: int = 0
    ) -> None:
        """Основной метод получения данных с API ресурса"""
        _range = ranges.pop(0)
        session = sync_session()
        # header = {
        #     'Range' : range
        # }
        try:
            url = self.request_builder(self.table_name, 
                f'{self.filter}&limit={self.limit}&offset={_range}') if self.filter \
                    else self.request_builder(self.table_name, 
                f'limit={self.limit}&offset={_range}')
            global content
            async with ScraperSession(timeout=get_content_timeout) as client:
                content = await client.get_json(
                    #headers=header,
                    url=url
                )
            if content:
                if not isinstance(content, list):
                    raise ValueError(content)
                await self.asyncpg_insert(content)
                #await self.write_to_base(content)
        except Exception as ex:
            logger.error(f"Произошла ошибка при получении данных для таблицы {self.table_name_disp} \
                в диапазоне {_range}: {ex}")
            raise ex
        finally:
            if ranges:
                scheduler = scheduler_service.get_scheduler()
                id = job_crud.get_prepared_job(session, parent_id, scheduler)
                try:
                    scheduler.add_job(
                        self.get_content_wraper,
                        id = id,
                        name=f'{self.table_name_disp} {ranges[0]}',
                        misfire_grace_time=None,
                        args=[ranges, parent_id]
                    )
                except Exception as ex:
                    logger.error(f"Произошла ошибка при назначении следующей задачи для таблицы {self.table_name_disp} \
                        : {ex}")
                    raise ex
            session.close()         
            # if len(ranges) > 0:
            #     #await asyncio.sleep(delay)
            #     session = sync_session()
            #     scheduler = scheduler_service.get_scheduler()
            #     id = job_crud.get_prepared_job(session, parent_id, scheduler)
            #     scheduler.add_job(
            #         self.get_content_wraper,
            #         id = id,
            #         name=f'{self.table_name_disp} {ranges[-1]}',
            #         misfire_grace_time=None,
            #         args=[ranges, parent_id]
            #     )


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
                    "crossed_price": stmt.excluded.crossed_price,
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
            stmt = Updater.make_sql_nu(self.table_name) if self.nu else \
                Updater.make_sql(self.table_name)
            await conn.executemany(
                stmt, 
                values
            )
        except Exception as ex:
            logger.error(f"Ошибка при комите: {ex}")
            raise ex
        finally:
            await conn.close()

    async def clear_table(self):
        """Очистить таблицу"""
        conn: asyncpg.connection.Connection \
            = await asyncpg.connect(dsn=settings.SQLALCHEMY_DATABASE_URI)
        try:
            
            stmt = f'''truncate nu_{self.table_name.replace('_', '')};'''
            await conn.execute(stmt)
        except Exception as ex:
            logger.error(f"Ошибка при очистке nu_{self.table_name}: {ex}")
            raise ex
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
            ON CONFLICT ON CONSTRAINT web_price_id_product_name_unique\
            DO NOTHING;'''
            return sql   
        if table_name == "rtpi_price":
            sql = '''INSERT INTO rtpiprice (web_price_id, date_observe, stock_status, current_price, crossed_price, contributor_id) \
            VALUES ($1,to_timestamp($2, 'YYYY-MM-DD T HH24:MI:SS:MS'),$3,$4,$5,$6) \
            ON CONFLICT ON CONSTRAINT web_price_id_date_observe_unique \
            DO NOTHING;'''
            return sql

    @staticmethod
    def make_sql_nu(table_name: str):
        if table_name == "rtpi_store_id":
            sql = '''INSERT INTO nu_rtpistoreid (store_id, store_name) \
            VALUES ($1,$2); '''
            return sql
        if table_name == "rtpi_price_page":
            sql = '''INSERT INTO nu_rtpipricepage (web_price_id, price_name, price_url, date_add, date_last_crawl, date_last_in_stock, rosstat_id, contributor_id, store_id, city_code) \
            VALUES ($1,$2,$3,to_timestamp($4, 'YYYY-MM-DD T HH24:MI:SS:MS'),to_timestamp($5, 'YYYY-MM-DD T HH24:MI:SS:MS'),to_timestamp($6, 'YYYY-MM-DD T HH24:MI:SS:MS'),$7,$8,$9,$10); '''
            return sql
        if table_name == "rtpi_product_name":
            sql = '''INSERT INTO nu_rtpiproductname (web_price_id, product_name, contributor_id, moment) \
            VALUES ($1,$2,$3,to_timestamp($4, 'YYYY-MM-DD T HH24:MI:SS:MS'));'''
            return sql   
        if table_name == "rtpi_price":
            sql = '''INSERT INTO nu_rtpiprice (web_price_id, date_observe, stock_status, current_price, crossed_price, contributor_id) \
            VALUES ($1,to_timestamp($2, 'YYYY-MM-DD T HH24:MI:SS:MS'),$3,$4,$5,$6);'''
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

    def produce_jobs(self, table_count: int, parent_id: str):
        """Создание задач"""
        try:
            session = None
            scheduler = scheduler_service.get_scheduler()
            _max = int(settings.MAX_CONCURENT_JOBS)
            _ranges = JobHelper.make_range_list(table_count, _max)
            jobs_amount = sum(len(x) for x in _ranges)
            JobHelper.create_child_jobs(parent_id, jobs_amount)
            session = sync_session()
            db_parent_job = job_crud.get(session, parent_id)
            if not db_parent_job:
                raise Exception('В базе отсутсвует основная задача, ' + 
                'невозможно получить дочерние')
            for idx, ranges in enumerate(_ranges):
                if len(ranges) > 0:
                    child_job_id = db_parent_job.child_jobs[idx].id
                    scheduler.add_job(
                        self.get_content_wraper,
                        id=child_job_id,
                        name=f'{self.table_name_disp} {ranges[0]}',
                        misfire_grace_time=None,
                        args=[ranges, parent_id]
                    )
            while not db_parent_job.time_completed:
                time.sleep(10)
                session.refresh(db_parent_job)
        except Exception as ex:
            raise ex
        finally: 
            if session:
                session.close()

    def get_content_wraper(self, *args):
        asyncio.run(self.get_content(*args))

async def update_table(
    table_name: str,
    self_id: str,
    non_unique: bool = False,
    fetch_all: bool = False
):
    """Обновить указанную таблицу"""
    try:        
        updater = Updater(table_name, non_unique)
        order_filter = updater.get_order_filter()
        update_filter = None if fetch_all or non_unique else \
            updater.make_update_filter(updater.get_last_date())
        count = await updater.get_table_count(table_name, update_filter)
        assert count != None
        if non_unique:
            await updater.clear_table()
        #updater.url = Updater.request_builder(table_name, filter)
        updater.filter = '&'.join([order_filter, update_filter]) \
            if order_filter and update_filter else \
                order_filter or update_filter
        updater.produce_jobs(count, self_id)
    except AssertionError as ex:
        #logger.error(f"При обновлении таблицы {table_name} не удалось получить кол-во строк")
        raise Exception(f"При обновлении таблицы {table_name} не удалось получить кол-во строк")
    except Exception as ex:
        #logger.error(f"При обновлении таблицы {table_name} произошла ошибка {ex}")
        raise ex

async def update_all(
    non_unique: bool,
    fetch_all: bool,
    parent_id: str
):
    """Обновление всех таблиц"""
    try:
        scheduler = scheduler_service.get_scheduler()
        await JobHelper.create_child_jobs_async(parent_id, len(tables))
        session = sync_session()
        db_parent_job = job_crud.get(session, parent_id)
        if not db_parent_job:
                raise Exception('В базе отсутсвует основная задача, ' + 
                'невозможно получить дочерние')
        for idx, table in enumerate(tables):
            child_job_id = db_parent_job.child_jobs[idx].id
            job_name = f'nu_update_{table}' if non_unique else \
                f'update_{table}'
            scheduler.add_job(
                update_wraper,
                id=child_job_id,
                name=job_name,
                misfire_grace_time=None,
                args=[table, child_job_id, non_unique, fetch_all]
            )
        while not db_parent_job.time_completed:
            await asyncio.sleep(10)
            session.refresh(db_parent_job)
    except Exception as ex:
        logger.error('При обновлении всех таблиц ' +
        f'произошла ошибка {ex}')
    finally:
        session.close()


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
        args_list.pop()
        end_time = datetime.datetime.now()
        print(f"Прождали {end_time-start_time} сек, начали {start_time}, закончили {end_time}")
    except Exception as ex:
        raise ex
    finally:
        try:
            if len(args_list) > 0:
                await asyncio.sleep(delay)
                scheduler = scheduler_service.get_scheduler()
                JobHelper.try_to_add_prepared_job(
                    parent_id=parent_id,
                    session=session,
                    scheduler=scheduler,
                    func=test_job_wrapper,
                    misfire_grace_time=None,
                    args=[args_list, delay, parent_id]                
                )
        except Exception as ex:
            logger.error(f'При попытке создать новую задачу возникла ошибка: {ex}')
            raise ex
        finally:
            session.close()

def update_all_wraper(*args):
    asyncio.run(update_all(*args))

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
        db_parent_job = job_crud.get(session, parent_id)
        if not db_parent_job:
            raise Exception('В базе отсутсвует основная задача, ' + 
            'невозможно получить дочерние')
        for idx, inner_list in enumerate(splited_list):
            child_job_id = db_parent_job.child_jobs[idx].id
            scheduler.add_job(
                test_job_wrapper,
                id = child_job_id,
                args=[inner_list, 0, parent_id],
                misfire_grace_time=None
            )
        while not db_parent_job.time_completed:
            time.sleep(10)
            session.refresh(db_parent_job)
    except Exception as ex:
        raise ex
    finally:
        session.close()
    
def test_job_wrapper(
        args_list: list = None, 
        delay: int = 0, 
        parent_id: str = None
    ):
        asyncio.run(test_coroutine_job(args_list, delay, parent_id))

def jobs_clean_up():
    """Удаление старых, застывших, пустых задач"""
    try:
        session = sync_session()
        job_list = []
        job_list.extend(job_crud.get_empty_jobs(session))
        job_list.extend(job_crud.get_stalled_jobs(session))
        job_list.extend(job_crud.get_old_completed_jobs(session))
        for job in job_list:
            session.delete(job)
        session.commit()
    except Exception as ex:
        raise ex
    finally: 
        session.close()