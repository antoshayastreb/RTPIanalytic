from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import logging
from datetime import timedelta
from typing import Optional

from scraper.models import Job as PersistanceJob
from scraper.utils.exeptions.scheduler import JobNotFoundException
from .base_crud import CRUDBase
from scraper.schemas.job import *

logger = logging.getLogger(__name__)

class JobCrud(CRUDBase[PersistanceJob, JobCreate, JobUpdate]):
    def get_job_extended_info(
        self, session: Session, id: str) -> Optional[JobOutExtendedInfo]:
        """Получить детальную информацию по задаче"""
        return session.query(self.model).filter(self.model.id == id).first()


async def get_job_by_id_async(
    job_id: str,
    session: AsyncSession
) -> 'PersistanceJob | None':
    """Получить задачу из базы по id"""
    try:
        result = await session.execute(
            select(PersistanceJob)
            .where(PersistanceJob.id == job_id)
            .options(selectinload(PersistanceJob.child_jobs)))
        job = result.scalar_one_or_none()
        assert job != None
        return job
    except Exception as ex:
        if isinstance(ex, AssertionError):
            raise JobNotFoundException
        else:
            logger.error(f"При получении задачи с id {job_id} " + 
            f"произошла ошибка: {ex}")
            return None

def get_job_by_id(
    job_id: str,
    session: Session
) -> 'PersistanceJob | None':
    """Получить задачу из базы по id"""
    try:
        job = session.get(PersistanceJob, job_id)
        assert job != None
        return job
    except Exception as ex:
        if isinstance(ex, AssertionError):
            raise JobNotFoundException
        else:
            logger.error(f"При получении задачи с id {job_id} " + 
            f"произошла ошибка: {ex}")
            return None

async def get_job_estimated_time_async(
    job_id: str,
    session: AsyncSession
) -> 'timedelta | None':
    """Получить расчетное время задачи"""
    job = await get_job_by_id_async(job_id, session)
    if job != None:
        return job.child_jobs_amount
    return None

def get_job_estimated_time(
    job_id: str,
    session: Session
) -> 'timedelta | None':
    """Получить расчетное время задачи"""
    job = get_job_by_id(job_id, session)
    if job != None:
        return job.estimated_time
    return None

def get_job_progress(
    job_id: str,
    sesssion: Session
) -> int:
    """Получить прогресс задачи"""
    job = get_job_by_id(job_id, sesssion)


job_crud = JobCrud(PersistanceJob)