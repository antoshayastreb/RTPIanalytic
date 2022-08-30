from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


from scraper.config import settings

sync_engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo= settings.SESSION_ECHO.lower() == 'true'
)

async_engine = create_async_engine(
    settings.ASYNC_SQLALCHEMY_DATABASE_URI,
    future=True,
    echo= settings.SESSION_ECHO.lower() == 'true' #кошмар
)

async_session = sessionmaker(
    async_engine, class_=AsyncSession,
    expire_on_commit=False
)

sync_session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_sync_session():
    db = sync_session()
    try:
        yield db
    finally:
        db.close()
