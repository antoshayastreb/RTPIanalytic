from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Text,
    DateTime,
    UniqueConstraint
)

from db.base_class import Base

class RtpiPrice(Base):
    id = Column(Integer, primary_key=True, index=True)
    web_price_id = Column(BigInteger, index=True)
    date_observe = Column(DateTime)
    stock_status = Column(Text, index=True)
    current_price = Column(BigInteger)
    crosssed_price = Column(BigInteger)
    contributor_id = Column(Integer)

    #Уникальность по 'web_price_id' и 'date_observe'
    __table_args__ = (
        UniqueConstraint('web_price_id', 'date_observe', name='web_price_id_date_observe_unique'),
    )