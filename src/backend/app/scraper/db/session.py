from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from scraper.config import settings

async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    future=True,
    echo=bool(settings.SESSION_ECHO)
)

async_session = sessionmaker(
    async_engine, class_=AsyncSession,
    expire_on_commit=False
)