from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from config import settings

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.SQLALCHEMY_DATABASE_URI)
}

executors = {
    # 'default': ThreadPoolExecutor(20),
    # 'processpool': ProcessPoolExecutor(4)
    #'default': ProcessPoolExecutor(4)
}

# job_defaults = {
#     #'coalesce': settings.COALESCE.lower() == 'true',
#     #'max_instances': 10
# }
job_defaults = {
    'misfire_grace_time': None
}

scheduler_type = AsyncIOScheduler
