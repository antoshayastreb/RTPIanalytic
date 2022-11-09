import datetime

class SerializerHelper:
    """Сборник вспомогательных функций для сериализации"""
    @staticmethod
    def convert_datetime_to_iso_8601(dt: datetime) -> str:
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    @staticmethod
    def convert_timedelta_to_seconds(td: datetime.timedelta) -> int:
        return td.seconds