"""Workout and erg session data models."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class Workout(Base):
    """A single erg training session with all Concept2 metrics."""

    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Workout identification
    workout_type: Mapped[str] = mapped_column(String(50), nullable=False)  # steady_state, interval, test, etc.
    description: Mapped[str | None] = mapped_column(Text)  # e.g. "4x2k r3:00" or "60min SS"
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual, concept2_api

    # Distance and duration
    total_distance_m: Mapped[int | None] = mapped_column(Integer)
    total_time_seconds: Mapped[float | None] = mapped_column(Float)

    # Primary performance metrics (Tier 1)
    avg_split_seconds: Mapped[float | None] = mapped_column(Float)  # per 500m, in seconds
    avg_watts: Mapped[float | None] = mapped_column(Float)
    avg_spm: Mapped[float | None] = mapped_column(Float)  # strokes per minute
    avg_drive_length_m: Mapped[float | None] = mapped_column(Float)
    avg_distance_per_stroke_m: Mapped[float | None] = mapped_column(Float)
    drag_factor: Mapped[int | None] = mapped_column(Integer)

    # Heart rate (Tier 2)
    avg_hr: Mapped[int | None] = mapped_column(Integer)
    max_hr: Mapped[int | None] = mapped_column(Integer)

    # Subjective (Tier 2)
    rpe: Mapped[int | None] = mapped_column(Integer)  # 1-10

    # Calculated training load
    trimp: Mapped[float | None] = mapped_column(Float)  # Training Impulse
    time_in_zone_1_seconds: Mapped[float | None] = mapped_column(Float)
    time_in_zone_2_seconds: Mapped[float | None] = mapped_column(Float)
    time_in_zone_3_seconds: Mapped[float | None] = mapped_column(Float)
    time_in_zone_4_seconds: Mapped[float | None] = mapped_column(Float)
    time_in_zone_5_seconds: Mapped[float | None] = mapped_column(Float)

    # Concept2 logbook reference
    concept2_id: Mapped[str | None] = mapped_column(String(50), unique=True)

    notes: Mapped[str | None] = mapped_column(Text)


class WorkoutInterval(Base):
    """Individual intervals/splits within a workout."""

    __tablename__ = "workout_intervals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workout_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    interval_number: Mapped[int] = mapped_column(Integer, nullable=False)

    distance_m: Mapped[int | None] = mapped_column(Integer)
    time_seconds: Mapped[float | None] = mapped_column(Float)
    split_seconds: Mapped[float | None] = mapped_column(Float)  # per 500m
    watts: Mapped[float | None] = mapped_column(Float)
    spm: Mapped[float | None] = mapped_column(Float)
    avg_hr: Mapped[int | None] = mapped_column(Integer)
    max_hr: Mapped[int | None] = mapped_column(Integer)
    rest_seconds: Mapped[float | None] = mapped_column(Float)
