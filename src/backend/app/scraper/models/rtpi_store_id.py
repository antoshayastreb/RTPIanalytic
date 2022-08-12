from sqlalchemy import (
    Integer,
    Column,
    BigInteger,
    String,
)

from db.base_class import Base

class Rtpi_Store_Id(Base):
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, index=True)
    store_name = Column(String(256), unique=True)

    # __ts_vector__ = Column(TSVector(),
    #                           Computed("to_tsvector('russian', store_name || '')",
    #                                       persisted=True))
    # __table_args__ = (
    #     Index('ix_store_name___ts_vector__', __ts_vector__, postgresql_using='gin'),
    # )