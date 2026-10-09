"""
SQLAlchemy engine + session setup. Works with SQLite out of the box.
To move to PostgreSQL later, just change DATABASE_URL in .env —
nothing else in the codebase needs to change.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates all tables. Safe to call repeatedly."""
    import backend.models  # noqa: F401  (ensures models are registered)
    Base.metadata.create_all(bind=engine)
