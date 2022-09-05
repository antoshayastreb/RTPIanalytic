from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from scraper.models import (
    Table
)

router = APIRouter()

@router.get(
    "/get_available_tables",
    response_model=List[str]
)
async def get_tables():
    """Получить доуступные для обновления таблицы"""
    return [table.value for table in Table]