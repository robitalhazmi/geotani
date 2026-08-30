"""Database connection and session management for GeoTani API."""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DEFAULT_DB_URL = "postgresql://geotani:geotani_dev@localhost:5432/geotani"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency injection helper yielding a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
