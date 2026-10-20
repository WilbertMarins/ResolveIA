"""SQLAlchemy engine and session factory construction."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

type SessionFactory = async_sessionmaker[AsyncSession]


def create_database(database_url: str) -> tuple[AsyncEngine, SessionFactory]:
    """Create the engine and session factory without opening a connection."""
    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory
