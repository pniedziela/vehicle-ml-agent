"""Database engine and session configuration."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base


def _build_database_url(raw_url: str) -> str:
    """Normalise the DATABASE_URL for async SQLAlchemy.

    Railway (and Heroku) provide URLs like ``postgres://user:pass@host/db``.
    SQLAlchemy 2.x requires ``postgresql+asyncpg://...`` for async PG.
    """
    url = raw_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_db_url = _build_database_url(settings.DATABASE_URL)

# For SQLite we need check_same_thread=False; for PG it's not needed.
_connect_args: dict = {}
if _db_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(_db_url, echo=False, connect_args=_connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI – yields a database session."""
    async with async_session() as session:
        yield session
