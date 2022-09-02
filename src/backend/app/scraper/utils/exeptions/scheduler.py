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

class MaxJobInstancesReached(Exception):
    """
    Достигнуто предельно допустимое количество
    одновременно запущенных задач.
    """
    def __init__(self, 
        job_name: str, 
        already_in: int, 
        max_for_job: int, 
        *args: object
    ) -> None:
        super().__init__(*args)
        self.job_name = job_name
        self.already_in = already_in
        self.max_for_job = max_for_job 
    # def __init__(self, job_name: str, already_in: int, max_for_job: int) -> None:
    #     self.job_name = job_name
    #     self.already_in = already_in
    #     self.max_for_job = max_for_job 

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