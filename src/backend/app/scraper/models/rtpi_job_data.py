from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    BigInteger,
    Boolean
)

from db.base import Base

class RtpiJobData(Base):
    """Класс для хранения данных rtpi задач"""
    id = Column(Integer, primary_key=True, index=True)
    job_info_id = Column(Integer)
    table_name = Column(String(100))
    filter = Column(Text)
    offset = Column(BigInteger)
    limit = Column(BigInteger)
    #Показатель того, что эта строка была прочитана
    taken = Column(Boolean, index=True)
