class SchedulerAlreadyPausedException(Exception):
    """Шедулер уже приостановлен"""
    pass

class SchedulerAlreadyRunningException(Exception):
    """Шедулер уже возобновлен"""
    pass
class SchedulerStopedException(Exception):
    """Шедулер в данный момент остановлен"""
    pass
class JobNotFoundException(Exception):
    """
    Задача с указанным `job_id` не найдена.

    `job_id` - id задачи.
    """
    def __init__(self, job_id: str = 'job_id'):
        self.job_id = job_id + " id" \
            if job_id != 'job_id' else job_id
class Unsuccessful(Exception):
    """Неудачный запрос"""
    pass
class AllRetriesFailed(Exception):
    """Все попытки провалились"""
    pass