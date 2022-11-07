# import datetime
# from sqlalchemy import select, func
# from sqlalchemy.ext.hybrid import hybrid_property
# from sqlalchemy import (
#     Column,
#     String,
#     DateTime,
#     ForeignKey
# )
# from sqlalchemy.orm import (
#     relationship,
#     column_property
# )
# from sqlalchemy.dialects.postgresql import JSON, ARRAY

# from db.base import Base

# class Job(Base):
#     """Класс для хранения в базе информации о задачах"""
#     id = Column(String(191), primary_key=True, index=True)
#     name = Column(String)
#     #func = Column(String)
#     args = Column(ARRAY(String))
#     kwargs = Column(JSON)
#     time_started = Column(DateTime)
#     time_completed = Column(DateTime)
#     completion_time = column_property(time_completed - time_started)
#     exception_text = Column(String)
#     #pending = Column(Boolean)
#     # coalesce = Column(Boolean)
#     # max_instances = Column(Integer)
#     parent_job_id = Column(String(191), ForeignKey('job.id'))
#     parent_job = relationship(
#         'Job', 
#         back_populates='child_jobs', 
#         cascade='all',
#         remote_side=id,
#         lazy='selectin'
#     )
#     child_jobs = relationship('Job', back_populates='parent_job', lazy='selectin')

#     @hybrid_property
#     def child_jobs_amount(self) -> int:
#         """Общее количество дочерних задач"""
#         return len(self.child_jobs)

#     @child_jobs_amount.expression
#     def child_jobs_amount(cls) -> int:
#         return (
#             select([func.count(Job.id)])
#             .where(Job.parent_job_id == cls.id)
#             .label('child_jobs_amount')
#         )
    
#     @hybrid_property
#     def completed_child_jobs(self) -> 'list[Job]':
#         """Завершенные дочерние задач"""
#         return [job for job in self.child_jobs if job.time_completed]

#     @hybrid_property
#     def not_yet_started_child_jobs(self) -> 'list[Job]':
#         """Ещё не запускавшиеся дочерние задач"""
#         return [job for job in self.child_jobs if not job.time_started]

#     @hybrid_property
#     def started_child_jobs(self) -> 'list[Job]':
#         """
#         Дочерние задачи, чьё выполнение было запущено,
#         но ещё не завершилось
#         """
#         return [job for job in self.child_jobs \
#             if job.time_started and not job.time_completed]

#     @hybrid_property
#     def child_jobs_with_error(self) -> 'list[Job]':
#         """Дочерние задачи с ошибкой"""
#         return [job for job in self.completed_child_jobs \
#             if job.exception_text]

#     @hybrid_property
#     def completed_child_jobs_amount(self) -> int:
#         """Количество завершенных дочерних задач"""
#         return len(self.completed_child_jobs)

#     @hybrid_property
#     def not_yet_started_child_jobs_amount(self) -> int:
#         """Количество ещё не запускавшихся дочерних задач"""
#         return len(self.not_yet_started_child_jobs)

#     @hybrid_property
#     def started_child_jobs_amount(self) -> int:
#         """
#         Количество дочерних задач, чьё выполнение было запущено,
#         но ещё не завершилось
#         """
#         return len(self.started_child_jobs)

#     @hybrid_property
#     def total_child_jobs_amount(self) -> int:
#         """"
#         Общее количество дочерних задач, включая дочерние задачи
#         дочерних задач. 
#         """
#         # if self.child_jobs_amount == 0:
#         #     return 1
#         # return sum([job.total_child_jobs_amount
#         #     for job in self.child_jobs])
#         childs_total_sum = sum([job.total_child_jobs_amount
#             for job in self.child_jobs])
#         if childs_total_sum == 0:
#             return self.child_jobs_amount
#         return childs_total_sum + self.child_jobs_amount

#     @hybrid_property
#     def total_completed_jobs_amount(self) -> int:
#         """"
#         Общее количество завершенных дочерних задач, включая дочерние
#         задачи дочерних задач. 
#         """
#         # if self.child_jobs_amount == 0:
#         #     return 1
#         # return sum([job.total_completed_jobs_amount 
#         #     for job in self.completed_child_jobs])
#         childs_total_sum = sum([job.total_completed_jobs_amount
#             for job in self.completed_child_jobs])
#         if childs_total_sum == 0:
#             return self.completed_child_jobs_amount
#         return childs_total_sum + self.completed_child_jobs_amount

#     @hybrid_property
#     def child_jobs_with_error_amount(self) -> int:
#         """Количество дочерних задач с ошибкой"""
#         return len(self.child_jobs_with_error)

#     @hybrid_property
#     def total_job_progress(self) -> int:
#         """
#         Возвращает прогресс задачи в процентах по всем дочерним, включая
#         дочерние дочерних.
#         """
#         #return f'{self.total_completed_jobs_amount}/{self.total_child_jobs_amount}'
#         if self.total_child_jobs_amount == 0:
#             return 100 if self.time_completed else 0
#         if self.total_completed_jobs_amount == 0:
#             return 0
#         return round(self.total_completed_jobs_amount / self.total_child_jobs_amount \
#             * 100)

#     @hybrid_property
#     def job_progress(self) -> int:
#         """
#         Возвращает прогресс задачи в процентах.
#         """
#         #return f'{self.total_completed_jobs_amount}/{self.total_child_jobs_amount}'
#         if self.child_jobs_amount == 0:
#             return 100 if self.time_completed else 0
#         if self.completed_child_jobs_amount == 0:
#             return 0
#         return round(self.completed_child_jobs_amount / self.child_jobs_amount \
#             * 100)

#     @hybrid_property
#     def errors_amount(self) -> int:
#         """Возвращает количество ошибок, связанных с этой задачей"""
#         if self.child_jobs_amount == 0:
#             return 1 if self.exception_text else 0
#         return sum([job.errors_amount for job in self.completed_child_jobs])

#     @hybrid_property
#     def estimated_time(self) -> 'datetime.timedelta | None':
#         """
#         Расчетное время завершения задачи

#         Если у задачи нет дочерних задач, возвращает `None`.

#         Возвращает среднее время между завершенными задачами
#         умноженное на количество ещё незапущенных задач `not_yet_started_child_jobs_amount`.
#         """
#         if self.completion_time or self.child_jobs_amount == 0:
#             return self.completion_time
#         child_jobs_time = [
#             job.estimated_time for job in self.completed_child_jobs
#         ]
#         if len(child_jobs_time) == 0:
#             return None
#         return sum(child_jobs_time, datetime.timedelta()) // len(child_jobs_time) \
#             * self.not_yet_started_child_jobs_amount

#     def __repr__(self) -> str:
#         return "Job(name=%r, id=%r, parent_job_id=%r)" % (
#             self.name,
#             self.id,
#             self.parent_job_id
#         )

#     def is_all_childs_completed(self) -> bool:
#         """Проверка на завершенность всех дочерних задач"""
#         # if not any(self.child_jobs):
#         #     return True
#         if self.child_jobs_amount == 0:
#             return True
#         return self.completed_child_jobs_amount == self.child_jobs_amount
#         #return all([x.time_completed for x in self.child_jobs])

#     def set_complete_date(self) -> None:
#         """Установить дату заврешения задачи (пометить завершенной)"""
#         if self.is_all_childs_completed():
#             self.time_completed = datetime.datetime.now()
#             if self.parent_job:
#                 self.parent_job.set_complete_date()
            