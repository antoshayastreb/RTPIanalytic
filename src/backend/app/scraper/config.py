# import os
# from dotenv import load_dotenv

# #Базовые параметры
# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# load_dotenv(os.path.join(base_dir, '.env'))

# #Настраиваемые параметры

# #Развертывание
# status = os.getenv('STATUS', 'DEBUG')

# #Токен API
# rtpi_api_token = os.getenv('RTPI_API_TOKEN')

# #Базовый адрес запросов
# rtpi_api_url = os.getenv('RTPI_API_URL')

# #Адрес подключения базы данных
# database_url = os.getenv('DATABASE_URL') 

from typing import Optional, Dict, Any
from pydantic import BaseSettings, PostgresDsn, validator
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    VERSION: str = "0.1.5"
    #Стандартные эндпоинты
    API_V1_STR: str = "/api/v1"
    DOCS_URL: str = "/api/docs"
    #Наименование сервера
    SERVICE_NAME: str = "'Automatic' RTPI API scraper"
    #Настройки для подключения к базе
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    ASYNC_SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    #Отобрадать детализацию по каждому запросу
    SESSION_ECHO: Optional[str] = 'False'
    #Валидация строки подключения
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT") or '5432',
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    @validator("ASYNC_SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_async_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT") or '5432',
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    #Настройки API-источника 
    RTPI_API_TOKEN: str
    RTPI_REQUEST_BASEURL: str
    #Общее время ожидание запроса,
    #включающее соединение, отправку и чтение запроса
    CLIENT_TIMEOUT_GET_COUNT: str = '600' #секунд
    CLIENT_TIMEOUT_GET_CONTENT: str = '180'
    CLIENT_RETRY_ATTEMPTS: str = '3'
    #Настройки для APScheduler
    #MAX_INSTANCES: str = '4'
    #Настройка регулирующая сколько одновремно задач будет
    #запущено
    MAX_CONCURENT_JOBS: str = '2'
    COALESCE: str = 'True'
    #MAX_WORKERS: str = '4'
    TABLE_LIMIT: str = '100000'
    #Настройки для Pydantic BaseSettings
    class Config:
        env_file = '~/.env'
        case_sensitive = True

settings = Settings()        