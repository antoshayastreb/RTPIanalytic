from sqlalchemy.orm import Session
import logging
from typing import Optional
from apscheduler.schedulers.base import BaseScheduler

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

    def get_prepared_job(
            self,
            session: Session, 
            parent_id: str,
            scheduler: BaseScheduler = None
        ) -> Optional[JobOutExtendedInfo]:
        """Получить дочернюю задачу, чьё выполнение ещё не началось"""
        db_job = session.query(self.model).filter_by(parent_job_id = parent_id,
            time_started = None
        ).first()
        if not db_job:
            raise ValueError('Не найденно ни одной подготовленной задачи ' +
            f'для родительской задачи {parent_id}')
        if scheduler:
            job = scheduler.get_job(db_job.id)
            if job:
                return self.get_prepared_job(session, parent_id, scheduler)
        return db_job.id
        

job_crud = JobCrud(PersistanceJob)