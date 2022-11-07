from operator import index
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    BigInteger
)

from db.base import Base

class RtpiJobInfo(Base):
    """Класс для хранения информации об rtpi задачах"""
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(191), index=True)
    table_count = Column(BigInteger)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())
    #completed_count = Column(BigInteger)
    remained_count = Column(BigInteger)
