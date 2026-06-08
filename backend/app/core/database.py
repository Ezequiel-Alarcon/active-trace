from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


def create_engine(url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    db_url = url or settings.DATABASE_URL
    return create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def create_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker:
    if engine is None:
        engine = create_engine()
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


class Base(DeclarativeBase):
    pass