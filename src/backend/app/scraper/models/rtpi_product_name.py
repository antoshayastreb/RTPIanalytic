from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    UniqueConstraint,
    BigInteger
)

from db.base_class import Base

class RtpiProductName(Base):
    id = Column(Integer, primary_key=True, index=True)
    web_price_id = Column(BigInteger, index=True)
    product_name = Column(Text)
    contributor_id = Column(Integer)
    moment = Column(DateTime)

    # __ts_vector__ = Column(TSVector(),
    #                           Computed("to_tsvector('russian', product_name || '')",
    #                                       persisted=True))
    __table_args__ = (
        #Index('ix_productname___ts_vector__', __ts_vector__, postgresql_using='gin'),
        #Уникальность по 'web_price_id' и 'moment'
        UniqueConstraint('web_price_id', 'moment', name=f'web_price_id_moment_unique'),
    )