"""Database engine and session configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///data/training.db"


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from src.models import workout, wellness, benchmark, body, strength, nutrition, training_plan  # noqa: F401

    Base.metadata.create_all(bind=engine)
