import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import (
    relationship
)
from sqlalchemy.dialects.postgresql import JSON, ARRAY

from db.base import Base

class Job(Base):
    """Класс для хранения в базе информации о задачах"""
    id = Column(String(191), primary_key=True, index=True)
    name = Column(String)
    func = Column(String)
    args = Column(ARRAY(String))
    kwargs = Column(JSON)
    time_started = Column(DateTime)
    time_completed = Column(DateTime)
    #pending = Column(Boolean)
    # coalesce = Column(Boolean)
    # max_instances = Column(Integer)
    parent_job_id = Column(String(191), ForeignKey('job.id'))
    parent_job = relationship(
        'Job', 
        back_populates='child_jobs', 
        cascade='all',
        remote_side=id
    )
    child_jobs = relationship('Job', back_populates='parent_job')

    def __repr__(self) -> str:
        return "Job(name=%r, id=%r, parent_job_id=%r)" % (
            self.name,
            self.id,
            self.parent_job_id
        )

    # def append_child_job(self, job: 'Job'):
    #     """Добавить дочернюю задачу"""
    #     self.child_jobs[job.name] = job

    def is_all_childs_completed(self) -> bool:
        """Проверка на завершенность всех дочерних задач"""
        if not any(self.child_jobs):
            return True
        return all([x.time_completed for x in self.child_jobs])

    def set_complete_date(self) -> None:
        """Установить дату заврешения задачи (пометить завершенной)"""
        if self.is_all_childs_completed():
            self.time_completed = datetime.datetime.now()
            if self.parent_job:
                self.parent_job.set_complete_date()
            