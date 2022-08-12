from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Text,
    TIMESTAMP,
)

from db.base_class import Base

class RtpiPricePage(Base):
    id = Column(Integer, primary_key=True, index=True)
    web_price_id = Column(BigInteger, unique=True, index=True)
    price_name = Column(Text)
    price_url = Column(Text)
    date_add = Column(TIMESTAMP)
    date_last_in_stock = Column(TIMESTAMP)
    rosstat_id = Column(Integer)
    contributor_id = Column(Integer)
    store_id = Column(Integer)
    date_last_crawl = Column(TIMESTAMP)
    city_code = Column(BigInteger)