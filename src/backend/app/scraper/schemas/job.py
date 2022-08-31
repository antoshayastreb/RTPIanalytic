from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from scraper.utils.help_func import SerializerHelper

class JobBase(BaseModel):
    """Базовый класс информации о задаче"""
    id: str
    name: Optional[str]

class JobCreate(JobBase):
    """Класс для создания задачи"""
    func: Optional[str]
    args: Optional[List[str]]
    kwargs: Optional[str]

class JobUpdate(JobBase):
    """Класс редактирования задачи"""
    func: Optional[str]
    args: Optional[List[str]]
    kwargs: Optional[str]

class CurrentScheduledJob(JobBase):
    """Запланированная задача"""
    run_frequency: str
    next_run: str

class CurrentScheduledJobsResponse(JobBase):
    """Список запланированных задач"""
    jobs:List[CurrentScheduledJob]

class JobCreateDeleteResponse(JobBase):
    """Класс для создания/удаления задачи"""
    scheduled: bool

class JobOut(JobBase):
    """Базовая информация о задаче"""
    func: Optional[str]
    args: Optional[List[str]]
    kwargs: Optional[str]
    exception_text: Optional[str]
    time_started: Optional[datetime]
    time_completed: Optional[datetime]
    completion_time: Optional[timedelta]
    parent_job_id: Optional[str]
    total_job_progress: Optional[int]
    errors_amount: Optional[int]

    class Config:
        json_encoders = {
            #Перевод даты в строку
            datetime: SerializerHelper.convert_datetime_to_iso_8601 
        }
        
        orm_mode = True

class JobOutExtendedInfo(JobOut):
    """Расширенная информация о задаче"""
    job_progress: Optional[int]
    estimated_time: Optional[timedelta]
    child_jobs_amount: Optional[int]
    completed_child_jobs_amount: Optional[int]
    not_yet_started_child_jobs_amount: Optional[int]
    started_child_jobs_amount: Optional[int]
    total_child_jobs_amount: Optional[int]
    total_completed_jobs_amount: Optional[int]
    child_jobs: Optional[List[str]]
    completed_child_jobs: Optional[List[str]]
    not_yet_started_child_jobs: Optional[List[str]]
    started_child_jobs: Optional[List[str]]
    child_jobs_with_error: Optional[List[str]]

    class Config:
        json_encoders = {
            #Перевод даты в строку
            datetime: SerializerHelper.convert_datetime_to_iso_8601,
            timedelta:  SerializerHelper.convert_timedelta_to_seconds
        }

        class getter_dict():
            def __init__(self, item):
                self.item = item

            def get(self, name, default=None):
                value = getattr(self.item, name, default)
                if isinstance(value, list) \
                    and name in (
                        'child_jobs',
                        'completed_child_jobs',
                        'not_yet_started_child_jobs',
                        'started_child_jobs',
                        'child_jobs_with_error'
                    ):
                    return [item.id for item in value]
                else:
                    return value