import logging
from fastapi import FastAPI

from config import settings
from scraper.scheduler_service import scheduler_service
from api.api_v1.api import api_router
from scraper.scheduler_service import register_scheduler_exceptions_handlers

#Инициализация приложения
app = FastAPI(
    title=settings.SERVICE_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version=settings.VERSION,
    docs_url=settings.DOCS_URL,
)

#Настройки логирования
logging.basicConfig(filename="scraperLog.log", level = logging.INFO)
logger = logging.getLogger( __name__ )

#Регистрация эндпоинтов
app.include_router(api_router, prefix=settings.API_V1_STR)

#Регистрация обработчкиов ошибок
register_scheduler_exceptions_handlers(app)

#Вызов функций на старте сервиса
@app.on_event("startup")
async def try_to_load_scheduler():
    """Создает шедулер"""
    scheduler = scheduler_service.instance
    #app.state.scheduler_service = scheduler
    try:
        scheduler.start()
        logger.info(" Шедулер запущен ")
    except Exception as ex:
        logger.error(f"Произошла ошибка при запуске шедулера {str(ex)}")

#Вызов функций на завершении сервиса
@app.on_event("shutdown")
async def try_to_shutdown_scheduler():
    """Завершает шедулер"""
    try:
        scheduler = scheduler_service.instance
        scheduler.shutdown(wait=False)
    except:
        pass