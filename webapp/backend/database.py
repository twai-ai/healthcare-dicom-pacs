"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from railway_env import resolve_database_url


def _normalize_database_url(url: str) -> str:
    """Railway and others often provide postgres://; SQLAlchemy needs postgresql://."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


# Database URL from environment variable (Railway: DATABASE_URL or DATABASE_PRIVATE_URL)
DATABASE_URL = _normalize_database_url(resolve_database_url())

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

