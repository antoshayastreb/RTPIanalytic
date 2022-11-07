import random
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.job import Job
from apscheduler.events import JobEvent
from apscheduler.events import (
    EVENT_JOB_SUBMITTED, 
    EVENT_JOB_EXECUTED, 
    EVENT_JOB_ERROR,
    EVENT_JOB_ADDED
)
import logging

from .config import (
    job_defaults,
    executors,
    jobstores,
    scheduler_type
)


logger = logging.getLogger(__name__)

class SchedulerService(object):

    def __init__(self) -> None:
        self.__running_jobs = {}
        self.__pending_jobs = {}
        self.__running_tasks = {}
        self.instance : BaseScheduler = scheduler_type()
        self.number = random.randint(1, 10)

        self.instance.configure(
            job_defaults = job_defaults,
            executors = executors,
            jobstores = jobstores
        )

        def count_same_jobs(
            job: Job,
            dict_to_search: dict
        ):
            """
            Подсчитать количество экземпляров задач
            в указанном словаре
            """
            if len(dict_to_search) == 0:
                return 0
            return sum(map(lambda x : x == job.name, dict_to_search.values()))

        #event listeners
        def job_submit(event: JobEvent):
            if event.job_id in self.__pending_jobs:
                j_value = self.__pending_jobs.pop(event.job_id)
                if j_value:
                    self.__running_jobs[event.job_id] = j_value

        def job_remove(event: JobEvent):
            if event.job_id in self.__running_jobs:
                self.__running_jobs.pop(event.job_id)
        
        def job_add(event: JobEvent):
            job = self.instance.get_job(event.job_id)
            #Костыльное решение с + 1, так как в момент добавления задачи 
            #из предыдущей задачи, количество будет равно кол-ву max_instances
            if count_same_jobs(job, self.__running_jobs) >= job.max_instances + 1 \
                or count_same_jobs(job, self.__pending_jobs) >= job.max_instances + 1:
                self.instance.remove_job(event.job_id)
            elif job.id not in self.__pending_jobs:
                self.__pending_jobs[job.id] = job.name

            # if (sum(map(lambda x : x == event.job_id, self.instance._pending_jobs)))
            # if event.job_id in self.__running_jobs and \
            #     sum(map(lambda x : x == event.job_id, self.__running_jobs)) < job.max_instances:
            #     self.instance.modify_job()
            # print(job)

        self.instance.add_listener(job_add, EVENT_JOB_ADDED)
        self.instance.add_listener(job_submit, EVENT_JOB_SUBMITTED)
        self.instance.add_listener(job_remove, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

    def get_running_jobs(self):
        return self.__running_jobs

scheduler = SchedulerService()