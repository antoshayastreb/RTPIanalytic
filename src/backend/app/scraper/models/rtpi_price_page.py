from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Text,
    DateTime,
    UniqueConstraint
)

from db.base_class import Base

class RtpiPricePage(Base):
    id = Column(Integer, primary_key=True, index=True)
    web_price_id = Column(BigInteger, index=True)
    price_name = Column(Text)
    price_url = Column(Text)
    date_add = Column(DateTime)
    date_last_in_stock = Column(DateTime)
    rosstat_id = Column(Integer)
    contributor_id = Column(Integer)
    store_id = Column(Integer)
    date_last_crawl = Column(DateTime)
    city_code = Column(BigInteger)

    __table_args__ = (
        UniqueConstraint('web_price_id', name='web_price_id_unique'),
    )