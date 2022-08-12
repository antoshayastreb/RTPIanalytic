from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Request


class SchedulerService():
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
    
    def __str__(self) -> str:
        return "APSchedulerService"
    
    def get_scheduler(self) -> AsyncIOScheduler:
        return self.scheduler



def get_scheduler(request: Request) -> AsyncIOScheduler:
    return request.app.state.scheduler_service