"""Strength training data models (Tier 5)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class StrengthSession(Base):
    """A single strength training session."""

    __tablename__ = "strength_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    notes: Mapped[str | None] = mapped_column(Text)


class StrengthExercise(Base):
    """Individual exercise within a strength session."""

    __tablename__ = "strength_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    exercise_name: Mapped[str] = mapped_column(String(100), nullable=False)  # deadlift, back_squat, etc.
    sets: Mapped[int | None] = mapped_column(Integer)
    reps: Mapped[int | None] = mapped_column(Integer)
    weight_lbs: Mapped[float | None] = mapped_column(Float)
    is_pr: Mapped[bool | None] = mapped_column(Integer, default=False)  # SQLite boolean
    notes: Mapped[str | None] = mapped_column(Text)


class StrengthBenchmark(Base):
    """Periodic strength test results (1RM or 5RM)."""

    __tablename__ = "strength_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    exercise_name: Mapped[str] = mapped_column(String(100), nullable=False)
    test_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 1rm, 3rm, 5rm
    weight_lbs: Mapped[float] = mapped_column(Float, nullable=False)
    bodyweight_lbs: Mapped[float | None] = mapped_column(Float)  # for BW ratio calc
    bw_ratio: Mapped[float | None] = mapped_column(Float)  # weight / bodyweight
