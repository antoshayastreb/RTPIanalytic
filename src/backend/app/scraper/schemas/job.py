import datetime
from typing import Optional, List
from pydantic import BaseModel

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
    time_started: Optional[datetime.date]
    time_completed: Optional[datetime.date]
    completion_time: Optional[datetime.timedelta]
    parent_job_id: Optional[str]

    class Config:
        orm_mode = True

class JobOutExtendedInfo(JobOut):
    """Расширенная информация о задаче"""
    child_jobs: Optional[List[str]]
    child_jobs_amount: Optional[int]
    completed_child_jobs: Optional[List[str]]
    not_yet_started_child_jobs: Optional[List[str]]
    started_child_jobs: Optional[List[str]]
    completed_child_jobs_amount: Optional[int]
    not_yet_started_child_jobs_amount: Optional[int]
    started_child_jobs_amount: Optional[int]
    total_child_jobs_amount: Optional[int]
    total_completed_jobs_amount: Optional[int]
    total_job_progress: Optional[int]
    job_progress: Optional[int]
    estimated_time: Optional[datetime.timedelta]

    class Config:
        orm_mode = True

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
                        'started_child_jobs'
                    ):
                    return [item.id for item in value]
                else:
                    return value