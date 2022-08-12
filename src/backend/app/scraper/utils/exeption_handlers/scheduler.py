from fastapi import Request, HTTPException, status, FastAPI
from fastapi.responses import JSONResponse
from typing import Any, Optional, Dict

class SchedulerAlreadyPausedException(HTTPException):
    """Шедулер уже приостановлен"""
    def __init__(self, status_code: int = status.HTTP_409_CONFLICT, 
    detail: Any = None, 
    headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code, detail, headers)

class SchedulerAlreadyRunningException(HTTPException):
    """Шедулер уже возобновлен"""
    def __init__(self, status_code: int = status.HTTP_409_CONFLICT, 
    detail: Any = None, 
    headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code, detail, headers)

class SchedulerStopedException(HTTPException):
    """Шедулер в данный момент остановлен"""
    def __init__(self, status_code: int = status.HTTP_409_CONFLICT, 
    detail: Any = None, 
    headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code, detail, headers)

class JobNotFoundException(HTTPException):
    """Задача с указанным `job_id` не найдена"""
    def __init__(self, status_code: int = status.HTTP_404_NOT_FOUND, 
    detail: Any = None, 
    headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code, detail, headers)

def scheduler_already_paused_handler(request: Request, exc: HTTPException):
    """Обработчик ошибки `SchedulerAlreadyPausedExceprion`"""
    return JSONResponse(status_code=exc.status_code,
    content={"message": "Шедулер уже приостановлен"})

def scheduler_already_running_handler(request: Request, exc: HTTPException):
    """Обработчик ошибки `SchedulerAlreadyRunningException`"""
    return JSONResponse(status_code=exc.status_code,
    content={"message": "Шедулер уже возобновлен"})

def scheduler_stoped_handler(request: Request, exc: HTTPException):
    """Обработчик ошибки `SchedulerStopedException`"""
    return JSONResponse(status_code=exc.status_code,
    content={"message": "Шедулер в данный момент остановлен"})

def job_not_found_handler(request: Request, exc: HTTPException):
    """Обработчик ошибки `JobNotFoundException`"""
    return JSONResponse(status_code=exc.status_code,
    content={"message": "Задача с указанным \'job_id\' не найдена"})

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