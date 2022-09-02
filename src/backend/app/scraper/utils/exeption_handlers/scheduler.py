from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from scraper.utils.exeptions.scheduler import *

def scheduler_already_paused_handler(request: Request, exc: SchedulerAlreadyPausedException):
    """Обработчик ошибки `SchedulerAlreadyPausedExceprion`"""
    return JSONResponse(status_code=status.HTTP_200_OK,
    content={"message": "Шедулер уже приостановлен"})

def scheduler_already_resumed_handler(request: Request, exc: SchedulerAlreadyResumedException):
    """Обработчик ошибки `SchedulerAlreadyResumedException`"""
    return JSONResponse(status_code=status.HTTP_200_OK,
    content={"message": "Шедулер уже возобновлен"})

def scheduler_already_running_handler(request: Request, exc: SchedulerAlreadyRunningException):
    """Обработчик ошибки `SchedulerAlreadyRunningException`"""
    return JSONResponse(status_code=status.HTTP_200_OK,
    content={"message": "Шедулер уже запущен"})

def scheduler_already_running_but_paused(request: Request, exc: ShedulerAlreadyRunningButPaused):
    """Обработчик ошибки `ShedulerAlreadyRunningButPaused`"""
    return JSONResponse(status_code=status.HTTP_200_OK,
    content={"message": "Шедулер уже запущен, но приостановлен"})

def scheduler_stoped_handler(request: Request, exc: SchedulerStopedException):
    """Обработчик ошибки `SchedulerStopedException`"""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT,
    content={"message": "Шедулер в данный момент остановлен"})

def max_job_instances_reached_handler(request: Request, exc: MaxJobInstancesReached):
    """Обработчик ошибки `MaxJobInstancesReached`"""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT,
    content={"message": f"Для задачи {exc.job_name} достигнут лимит одновременно запущенных. " + 
    f"Запущенно {exc.already_in} из {exc.max_for_job}"})

def job_not_found_handler(request: Request, exc: JobNotFoundException):
    """Обработчик ошибки `JobNotFoundException`"""
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
    content={"message": f"Задача с указанным {exc.job_id} не найдена"})

def register_scheduler_exceptions_handlers(app: FastAPI):
    """Регистрация обработчиков ошибок шедулера"""
    app.add_exception_handler(SchedulerAlreadyPausedException,
    scheduler_already_paused_handler)
    app.add_exception_handler(SchedulerAlreadyResumedException,
    scheduler_already_resumed_handler)
    app.add_exception_handler(SchedulerStopedException,
    scheduler_stoped_handler)
    app.add_exception_handler(JobNotFoundException,
    job_not_found_handler)
    app.add_exception_handler(SchedulerAlreadyRunningException,
    scheduler_already_running_handler)
    app.add_exception_handler(ShedulerAlreadyRunningButPaused,
    scheduler_already_running_but_paused)
    app.add_exception_handler(MaxJobInstancesReached,
    max_job_instances_reached_handler)