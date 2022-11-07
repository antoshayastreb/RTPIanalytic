from yarl import URL
from .job_helper import JobHelper
from .misc import Ordering

class RtpiJobHelper(JobHelper):
        
    tables = [
    # 'rtpi_price': RtpiPrice,
    # 'rtpi_store_id': RtpiStoreId,
    # 'rtpi_price_page': RtpiPricePage,
    # 'rtpi_product_name': RtpiProductName
    'rtpi_price',
    'rtpi_store_id',
    'rtpi_price_page',
    'rtpi_product_name'
    ]

    @staticmethod
    def get_order_filter(
        table_name: str,
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
        if table_name in [
            'rtpi_price',
            'rtpi_price_page',
            'rtpi_product_name'
            ]:
            return f'order=web_price_id{order.value}'
        return None

    @staticmethod
    def make_sql(table_name: str):
        '''Создать запрос на вставку данных в базу'''
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
            ON CONFLICT ON CONSTRAINT web_price_id_product_name_moment_unique\
            DO NOTHING;'''
            return sql   
        if table_name == "rtpi_price":
            sql = '''INSERT INTO rtpiprice (web_price_id, date_observe, stock_status, current_price, crossed_price, contributor_id) \
            VALUES ($1,to_timestamp($2, 'YYYY-MM-DD T HH24:MI:SS:MS'),$3,$4,$5,$6) \
            ON CONFLICT ON CONSTRAINT web_price_id_date_observe_unique \
            DO NOTHING;'''
            return sql

    @staticmethod
    def request_builder(table_name: str, filter: str = None) -> URL:
        """Конструктор запроса"""
        return URL(f'/{table_name}?{filter}') if filter \
            else URL(f'/{table_name}')

    @staticmethod
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