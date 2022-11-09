import asyncpg
from typing import Any
from sqlalchemy import select, desc
#import uuid

#import logging

from ..session import ScraperSession
from ..utils.rtpi_helper import RtpiJobHelper
from scraper.scheduler_service import scheduler_service
from scraper.scheduler_service.config import settings
from scraper.db.session import async_session
from scraper.models import (
    RtpiJobData,
    RtpiJobInfo,
    RtpiPrice,
    RtpiPricePage,
    RtpiProductName
)

def __spawn_get_data_jobs_job(
    **kwargs
):
    """Создать задачи на получение данных"""
    scheduler = scheduler_service.instance
    max_jobs = int(settings.MAX_CONCURENT_JOBS)
    for _ in range(max_jobs):
        scheduler.add_job(
            __get_data_job,
            max_instances=max_jobs
        )

async def create_update_table_job(
    table_name: str,
    fetch_all: bool = False,
    hard_filter: str = None,
    **kwargs
):
    """Создание задачи для обновления указанной таблицы"""
    try:
        async def get_table_count(
            table_name: str,
            filter: str = None
        ) -> int:
            """
            Получить кол-во записей из `table_name`

            `table_name` - наименование таблицы

            `filter` - фильтр запроса
            """
            try:
                if not filter:
                    filter = RtpiJobHelper.get_order_filter(table_name)
                url = RtpiJobHelper.request_builder(table_name, filter)
                global count
                async with ScraperSession() as client:
                    return await client.get_count(
                        url = url
                    )
            except Exception as e:
                #logger.error(f"Ошибка при получении кол-ва из таблицы {e}")
                raise e

        async def get_last_date_async(
            table_name: str
        ) -> str | None:
            """Получить последнюю дату из таблицы"""
            async with async_session() as session:
                try:
                    stmt = None
                    match table_name:
                        case 'rtpi_price_page':
                            stmt = select(RtpiPricePage.date_last_in_stock). \
                            order_by(desc(RtpiPricePage.date_last_in_stock)). \
                            limit(1)
                        case 'rtpi_product_name':
                            stmt = select(RtpiProductName.moment). \
                            order_by(desc(RtpiProductName.moment)). \
                            limit(1)
                        case 'rtpi_price':
                            stmt = select(RtpiPrice.date_observe). \
                            order_by(desc(RtpiPrice.date_observe)). \
                            limit(1)
                        case _:
                            None
                    if stmt:
                        return (await session.scalars(stmt)).first().strftime('%Y-%m-%dT%H:%M:%S')
                    return None
                except Exception as ex:
                    raise ex
                finally:
                    await session.close()        

        async def create_job(
            table_name: str,
            count: int,
            filter: str
        ):
            """Создание задачи"""
            limit = int(settings.TABLE_LIMIT)
            async with async_session() as session:
                try:
                    rtpi_job_info = RtpiJobInfo(
                        table_name = table_name,
                        table_count = count,
                        remained_count = count
                    )
                    session.add(rtpi_job_info)
                    await session.commit()
                    await session.refresh(rtpi_job_info)
                    job_info_id = rtpi_job_info.id
                    for iter in range(0, count, limit):
                        session.add(
                            RtpiJobData(
                                job_info_id = job_info_id,
                                table_name = table_name,
                                filter = filter,
                                offset = iter,
                                limit = limit
                            )
                        )
                    await session.commit()
                except Exception as ex:
                    raise ex
                finally:
                    await session.close()

        #Фильтр сортировки, нужен для того, чтобы
        #не вытягивать дубли. (Дубли все равно появляются)
        order_filter = RtpiJobHelper.get_order_filter(table_name)
        #Если передан 'hard_filter' игнорируем текущий данные в базе
        #то есть ситуация равносильная 'fetch_all = False'
        #иначе тянем последнюю дату по таблице из базы 
        update_filter = None if fetch_all or hard_filter else \
        RtpiJobHelper.make_update_filter(await get_last_date_async(table_name))
        #Собираем финальный фильтр
        final_filter = RtpiJobHelper.make_filter(
            order_filter,
            hard_filter,
            update_filter
        )
        count = await get_table_count(table_name, final_filter)
        assert count

        await create_job(table_name, count, final_filter)
        __spawn_get_data_jobs()
    except AssertionError as ex:
        raise Exception(f"При обновлении таблицы {table_name} не удалось получить кол-во строк")
    except Exception as ex:
        raise ex

async def __get_data_job(
    **kwargs
):
    """Основной метод получения информации из API"""
    async def asyncpg_insert(table_name: str, content: Any):
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
            stmt = RtpiJobHelper.make_sql(table_name)
            await conn.executemany(
                stmt, 
                values
            )
        except Exception as ex:
            #logger.error(f"Ошибка при комите: {ex}")
            raise ex
        finally:
            await conn.close()
    
    async def get_request_info() -> RtpiJobData | None:
        """
        Получает первую строку из RtpiJobData
        """
        # con = await asyncpg.connect(dsn=settings.SQLALCHEMY_DATABASE_URI)
        # async with con.transaction('LOCK TABLE'):
        rtpi_job_data: RtpiJobData = None
        async with async_session() as session:
            try:
                async with session.begin():
                    await session.execute(f"LOCK TABLE {RtpiJobData.__table__.name} IN ROW EXCLUSIVE MODE;")
                    # stmt = Select(RtpiJobData).filter(
                    #     RtpiJobData.table_name == table_name, RtpiJobData.job_info_id == job_info_id
                    # ).limit(1)
                    stmt = select(RtpiJobData).filter(RtpiJobData.taken == None).order_by(RtpiJobData.offset).limit(1)
                    rtpi_job_data = (await session.scalars(stmt)).one()
                    if rtpi_job_data:
                        rtpi_job_data.taken = True
                        #await session.delete(rtpi_job_data)
                return rtpi_job_data
            except Exception as ex: 
                return None
            finally:
                await session.close()

    async def update_job_info(
        rtpi_job_data: RtpiJobData
    ):
        """Обновляет задачу"""
        async with async_session() as session:
            try:
                rtpi_job_info: RtpiJobInfo = None
                #CHANGE ME
                #await session.delete(rtpi_job_data)
                async with session.begin():
                    await session.execute(f"LOCK TABLE {RtpiJobInfo.__table__.name} IN ROW EXCLUSIVE MODE;")
                    stmt = select(RtpiJobInfo).filter(RtpiJobInfo.id == rtpi_job_data.job_info_id)
                    rtpi_job_info = (await session.scalars(stmt)).one()
                    if rtpi_job_info:
                        remained_count = rtpi_job_info.remained_count - rtpi_job_data.limit
                        if remained_count < 0:
                            remained_count = 0
                        rtpi_job_info.remained_count = remained_count
                        session.add(rtpi_job_info)
                await session.delete(rtpi_job_data)
                await session.commit()
            except Exception as ex:
                raise ex
            finally:
                await session.close()

    async def get_content(
        rtpi_job_data: RtpiJobData
    ) -> None:
        """Основной метод получения данных с API ресурса"""
        try:
            final_filter = RtpiJobHelper.make_filter(
                rtpi_job_data.filter,
                f'limit={rtpi_job_data.limit}&offset={rtpi_job_data.offset}'
            )
            global content
            async with ScraperSession() as client:
                content = await client.get_json(
                    url=RtpiJobHelper.request_builder(
                        rtpi_job_data.table_name,
                        final_filter
                    )
                )
            if content:
                if not isinstance(content, list):
                    raise ValueError(content)
                await asyncpg_insert(rtpi_job_data.table_name, content)
                await update_job_info(rtpi_job_data)
        except Exception as ex:
            # logger.error(f"Произошла ошибка при получении данных для таблицы {self.table_name} \
            #     в диапазоне {_range}: {ex}")
            raise ex

    def schedule_self():
        """Запланировать ещё один экземпляр задачи"""
        scheduler = scheduler_service.instance
        scheduler.add_job(
            __get_data_job,
            max_instances=int(settings.MAX_CONCURENT_JOBS)
        )

    rtpi_job_data: RtpiJobData = await get_request_info()
    if rtpi_job_data:
        scheduler_service.add_updating_table_job(kwargs['job_id'], rtpi_job_data.id)
        await get_content(rtpi_job_data)
        scheduler_service.remove_updating_table_job(kwargs['job_id'])
        schedule_self()





