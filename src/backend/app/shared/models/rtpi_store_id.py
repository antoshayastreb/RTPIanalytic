from sqlalchemy import (
    Integer,
    Column,
    BigInteger,
    String,
    UniqueConstraint
)

from shared.db.base_class import Base

class NU_RtpiStoreId(Base):
    """Таблица rtpistoreid без проверки уникальности"""
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, index=True)
    store_name = Column(String(256))

class RtpiStoreId(Base):  
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, index=True)
    store_name = Column(String(256))
    # __ts_vector__ = Column(TSVector(),
    #                           Computed("to_tsvector('russian', store_name || '')",
    #                                       persisted=True))
    __table_args__ = (
        UniqueConstraint('store_name', name=f'store_name_unique'),
    )