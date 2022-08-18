from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from scraper.config import settings

async_engine = create_async_engine(
    settings.ASYNC_SQLALCHEMY_DATABASE_URI,
    future=True,
    echo= settings.SESSION_ECHO.lower() == 'true' #кошмар
)

async_session = sessionmaker(
    async_engine, class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session