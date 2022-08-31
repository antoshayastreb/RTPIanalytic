from sqlalchemy.orm import Session
import logging
from typing import Optional, List
from apscheduler.schedulers.base import BaseScheduler
from datetime import datetime, timedelta

from scraper.models import Job as PersistanceJob
from scraper.utils.exeptions.scheduler import JobNotFoundException
from .base_crud import CRUDBase
from scraper.config import settings
from scraper.schemas.job import *

logger = logging.getLogger(__name__)

class JobCrud(CRUDBase[PersistanceJob, JobCreate, JobUpdate]):
    def get_job_extended_info(
        self, session: Session, id: str) -> JobOutExtendedInfo:
        """Получить детальную информацию по задаче"""
        return session.query(self.model).filter(self.model.id == id).first()

    def get_prepared_job(
            self,
            session: Session, 
            parent_id: str,
            scheduler: BaseScheduler = None
        ) -> JobOutExtendedInfo:
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
    
    def get_stalled_jobs(
        self,
        session: Session,
    ) -> List[PersistanceJob]:
        """Получить застывшие задачи"""
        stalled_job_deletion = int(settings.DELETE_STALLED_JOB_AFTER)
        filter_time = datetime.now() - timedelta(
            minutes=stalled_job_deletion) 
        return session.query(self.model).filter_by(
            completion_time = None, parent_job_id = None).filter(
                PersistanceJob.time_started <= filter_time).all()

    def get_empty_jobs(
        self,
        session: Session
    ) -> List[PersistanceJob]:
        """Получить пустые задачи"""
        return session.query(self.model).filter_by(
            name = None, time_started = None, func = None,
            time_completed = None, args = None
        ).all()

    def get_old_completed_jobs(
        self,
        session: Session
    ) -> List[PersistanceJob]:
        """Получить старые завершенные задачи"""
        completed_job_deletion = int(settings.DELETE_COMPLETE_JOB_AFTER)
        filter_time = datetime.now() - timedelta(
            minutes=completed_job_deletion) 
        return session.query(self.model).filter_by(
            parent_job_id = None).filter(
                PersistanceJob.time_started <= filter_time
            ).all()
        

job_crud = JobCrud(PersistanceJob)