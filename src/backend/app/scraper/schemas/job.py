from typing import Optional, List
from pydantic import BaseModel

class JobBase(BaseModel):
    """Базовый класс схемы задачи"""
    job_id: str
    name: Optional[str]

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
    pass