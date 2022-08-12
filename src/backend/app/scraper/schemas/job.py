from typing import Optional, List
from pydantic import BaseModel

class JobBase(BaseModel):
    """Базовый класс схемы задачи"""
    job_id: str
    description: Optional[str]

class CurrentScheduledJob(JobBase):
    """Запланированная задача"""
    run_frequency: str
    next_run: str

class CurrentScheduledJobsResponse(BaseModel):
    """Список запланированных задач"""
    jobs:List[CurrentScheduledJob]

class JobCreateDeleteResponse(BaseModel):
    """Класс для создания/удаления задачи"""
    scheduled: bool