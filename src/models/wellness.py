"""Daily wellness check-in and recovery data models."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class DailyWellness(Base):
    """Daily wellness check-in (Tier 7 — 30-second form)."""

    __tablename__ = "daily_wellness"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Subjective ratings (1-10)
    fatigue: Mapped[int | None] = mapped_column(Integer)
    muscle_soreness: Mapped[int | None] = mapped_column(Integer)
    stress: Mapped[int | None] = mapped_column(Integer)
    mood: Mapped[int | None] = mapped_column(Integer)
    sleep_quality_subjective: Mapped[int | None] = mapped_column(Integer)

    notes: Mapped[str | None] = mapped_column(Text)


class RecoveryMetrics(Base):
    """Daily recovery data from wearables (Tier 4 — Whoop/Garmin)."""

    __tablename__ = "recovery_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Heart rate
    resting_hr: Mapped[int | None] = mapped_column(Integer)
    hrv_rmssd: Mapped[float | None] = mapped_column(Float)  # ms

    # Sleep
    sleep_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    sleep_quality_score: Mapped[float | None] = mapped_column(Float)  # 0-100 from wearable
    deep_sleep_minutes: Mapped[int | None] = mapped_column(Integer)
    rem_sleep_minutes: Mapped[int | None] = mapped_column(Integer)
    light_sleep_minutes: Mapped[int | None] = mapped_column(Integer)
    awake_minutes: Mapped[int | None] = mapped_column(Integer)

    # Whoop-specific
    whoop_recovery_score: Mapped[float | None] = mapped_column(Float)  # 0-100
    whoop_strain: Mapped[float | None] = mapped_column(Float)  # 0-21

    # Estimated
    vo2max_estimate: Mapped[float | None] = mapped_column(Float)

    source: Mapped[str | None] = mapped_column(String(50))  # whoop, garmin, manual
