import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.schedulers.base import (
    STATE_PAUSED,
    STATE_RUNNING,
    STATE_STOPPED
)

from scraper.utils.services.scheduler_service import scheduler_service
from scraper.utils.exeption_handlers.scheduler import (
    SchedulerAlreadyPausedException,
    SchedulerAlreadyRunningException,
    SchedulerAlreadyResumedException,
    ShedulerAlreadyRunningButPaused
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/pause", status_code=200)
async def pause_scheduler(
    scheduler: BaseScheduler = 
    Depends(scheduler_service.get_scheduler),
    run_check = 
    Depends(scheduler_service.scheduler_running_check)
    ):
    """Приостановка шедулера"""
    if scheduler.state == STATE_PAUSED:
        raise SchedulerAlreadyPausedException()
    try:
        scheduler.pause()
        return JSONResponse(
            content={"message" : "Шедулер успешно приостановлен"}
        )
    except Exception as e:
        logger.error(f"При приостановке шедулера возникла ошибка: {e}")
        raise HTTPException(status_code=409, 
        detail=f"Не удалось приостановить шедулер {e}")

@router.post("/resume", status_code=200)
async def resume_scheduler(
    scheduler: BaseScheduler = 
    Depends(scheduler_service.get_scheduler),
    run_check = 
    Depends(scheduler_service.scheduler_running_check)
    ):
    """Возобновление работы шедулера"""
    if scheduler.state == STATE_RUNNING:
        raise SchedulerAlreadyResumedException()
    try:
        scheduler.resume()
        return JSONResponse(
            content={"message" : "Шедулер возобновлен"}
        )
    except Exception as e:
        logger.error(f"При возобновлении шедулера возникла ошибка: {e}")
        raise HTTPException(status_code=409,
        detail=f"Не удалось возобновить шедулер: {str(e)}")

# @router.post("/shutdown", status_code=200)
# async def shutdown_scheduler(
#     scheduler: BaseScheduler = 
#     Depends(scheduler_service.get_scheduler),
#     run_check = 
#     Depends(scheduler_service.scheduler_running_check),
#     wait: bool = True
#     ):
#     """
#     Остановка шедулера.

#     :param bool wait: Дождаться завершения задач
#     """
#     try:
#         scheduler.shutdown(wait)
#         return JSONResponse(
#             content={"message": "Шедулер остановлен"}
#         )
#     except Exception as e:
#         logger.error(f"При остановке шедулера возникла ошибка: {e}")
#         raise HTTPException(
#             status_code=409,
#             detail=f"Не удалось остановить шедулер: {e}"
#         )

# @router.post("/start", status_code=200)
# async def start_scheduler(
#     scheduler: BaseScheduler = 
#     Depends(scheduler_service.get_scheduler),
#     paused: bool = False
#     ):
#     """
#     Старт шедулера.

#     :param bool paused: Запустить шедулер в приостановдленном \
#     состоянии
#     """
#     if scheduler.running:
#         if scheduler.state == STATE_PAUSED:
#             raise ShedulerAlreadyRunningButPaused
#         raise SchedulerAlreadyRunningException
#     try:
#         scheduler_service.__init__()
#         scheduler = scheduler_service.get_scheduler()
#         scheduler.start(paused)
#         return JSONResponse(
#             content={"message": "Шедулер запущен"}
#         )
#     except Exception as e:
#         logger.error(f"При старте шедулера возникла ошибка: {e}")
#         raise HTTPException(
#             status_code=409,
#             detail=f"Не удалось запустить шедулер: {e}"
#         )

@router.get("/health_check", status_code=200)
async def check_scheduler_state(
    scheduler: BaseScheduler = 
    Depends(scheduler_service.get_scheduler),
):
    """Проверка текущего состояния шедулера"""
    global message
    message = "Неизвестно"
    try:
        if scheduler.state == STATE_RUNNING:
            if scheduler.state == STATE_PAUSED:
                message = "Шедулер остановлен"
            message = "Шедулер запущен"
        if scheduler.state == STATE_STOPPED:
            message = "Шедулер остановлен"
        return JSONResponse(
            content={"message": message}
        )
    except Exception as e:
        logger.error(f"При проверки статуса шедулера возникла ошибка: {e}")
        raise HTTPException(
            status_code=409,
            detail=f"Не удалось получить статус шедулера: {e}"
        )
        