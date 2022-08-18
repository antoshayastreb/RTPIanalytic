from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from scraper.utils.exeptions.scheduler import *

def scheduler_already_paused_handler(request: Request, exc: SchedulerAlreadyPausedException):
    """Обработчик ошибки `SchedulerAlreadyPausedExceprion`"""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT,
    content={"message": "Шедулер уже приостановлен"})

def scheduler_already_running_handler(request: Request, exc: SchedulerAlreadyRunningException):
    """Обработчик ошибки `SchedulerAlreadyRunningException`"""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT,
    content={"message": "Шедулер уже возобновлен"})

def scheduler_stoped_handler(request: Request, exc: SchedulerStopedException):
    """Обработчик ошибки `SchedulerStopedException`"""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT,
    content={"message": "Шедулер в данный момент остановлен"})

def job_not_found_handler(request: Request, exc: JobNotFoundException):
    """Обработчик ошибки `JobNotFoundException`"""
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
    content={"message": f"Задача с указанным {exc.job_id} не найдена"})

def register_scheduler_exceptions_handlers(app: FastAPI):
    """Регистрация обработчиков ошибок шедулера"""
    app.add_exception_handler(SchedulerAlreadyPausedException,
    scheduler_already_paused_handler)
    app.add_exception_handler(SchedulerAlreadyRunningException,
    scheduler_already_running_handler)
    app.add_exception_handler(SchedulerStopedException,
    scheduler_stoped_handler)
    app.add_exception_handler(JobNotFoundException,
    job_not_found_handler)