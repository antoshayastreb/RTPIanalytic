from typing import List, Any

from scraper.config import settings

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