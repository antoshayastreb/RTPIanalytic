from typing import Optional, Dict, Any
from pydantic import BaseSettings, PostgresDsn, validator
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    VERSION: str = "0.1.6"
    #Стандартные эндпоинты
    API_V1_STR: str = "/api/v1"
    DOCS_URL: str = "/api/docs"
    #Наименование сервиса
    SERVICE_NAME: str = "'Automatic' RTPI API scraper"
    #Настройки для подключения к базе данных
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    ASYNC_SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    #Отображать детализацию по каждому запросу к базе данных
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
    #Время на получение данных
    CLIENT_TIMEOUT_GET_CONTENT: str = '180'
    CLIENT_RETRY_ATTEMPTS: str = '3'
    #Настройки для APScheduler
    JOBSTORE_TABLE: str = 'job_store'
    #Настройка, регулирующая сколько одновременных задач будет
    #запущено
    MAX_CONCURENT_JOBS: str = '2'
    UPDATE_MAX_INSTANCES: str = '1'
    CLEANUP_MAX_INSTANCES: str = '1'
    TEST_MAIN_MAX_INSTANCES: str = '1'
    COALESCE: str = 'True'
    #MAX_WORKERS: str = '4'
    TABLE_LIMIT: str = '100000'
    #Удалить задачу через ... минут
    DELETE_COMPLETE_JOB_AFTER: str = '1440'
    DELETE_STALLED_JOB_AFTER: str = '60'
    #Настройки для Pydantic BaseSettings
    class Config:
        env_file = '~/.env'
        case_sensitive = True

settings = Settings()        