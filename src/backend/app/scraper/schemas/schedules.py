from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime

class Interval(BaseModel):
    weeks: Optional[int]
    days: Optional[int]
    hours: Optional[int]
    minutes: Optional[int]
    seconds: Optional[int]
    start_date: Optional[Union[datetime, str]]
    end_date: Optional[Union[datetime, str]]
    #timezone: Optional[str]
    jitter: Optional[int]

class Cron(BaseModel):
    year: Optional[Union[int, str]]
    month: Optional[Union[int, str]]
    day: Optional[Union[int, str]]
    week: Optional[Union[int, str]]
    day_of_week: Optional[Union[int, str]]
    hour: Optional[Union[int, str]]
    minute: Optional[Union[int, str]]
    second: Optional[Union[int, str]]
    start_date: Optional[Union[datetime, str]]
    end_date: Optional[Union[datetime, str]]
    #timezone: Optional[str]
    jitter: Optional[int]

class Date(BaseModel):
    run_date: Optional[Union[datetime, str]]
    #timezone: Optional[str]