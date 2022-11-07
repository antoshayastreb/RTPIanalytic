class Unsuccessful(Exception):
    """Неудачный запрос"""
    pass

class SchedulerAlreadyPausedException(Exception):
    """Шедулер уже приостановлен"""
    pass

class ShedulerAlreadyRunningButPaused(Exception):
    """Шежулер запущен, но приостановлен"""
    pass

class SchedulerAlreadyResumedException(Exception):
    """Шедулер уже возобновлен"""
    pass

class SchedulerAlreadyRunningException(Exception):
    """Шедулер уже запущен"""
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