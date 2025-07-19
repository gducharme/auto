"""Database utilities for creating engines and sessions."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import get_database_url

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine instance."""
    global _engine
    if _engine is None:
        url = get_database_url()
        _engine = create_engine(
            url,
            connect_args=(
                {"check_same_thread": False} if url.startswith("sqlite") else {}
            ),
        )
    return _engine


def SessionLocal() -> Session:
    """Return a new session bound to the engine from :func:`get_engine`."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return Session()


Base = declarative_base()
