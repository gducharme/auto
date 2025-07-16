"""Database utilities for creating engines and sessions."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

_engine = None


def get_database_url() -> str:
    """Return the database URL from ``DATABASE_URL`` or the default."""
    load_dotenv()
    return os.getenv("DATABASE_URL", "sqlite:///./substack.db")


def get_engine():
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


def SessionLocal():
    """Return a new session bound to the engine from :func:`get_engine`."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return Session()


Base = declarative_base()
