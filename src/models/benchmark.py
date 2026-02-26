"""Benchmark test results (Tier 3)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class BenchmarkTest(Base):
    """Results from standardized benchmark tests."""

    __tablename__ = "benchmark_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    test_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 2k, 6k, 30min, 500m, step

    # Results
    total_time_seconds: Mapped[float | None] = mapped_column(Float)  # for distance-based tests
    total_distance_m: Mapped[int | None] = mapped_column(Integer)  # for time-based tests (30min)
    avg_split_seconds: Mapped[float | None] = mapped_column(Float)  # per 500m
    avg_watts: Mapped[float | None] = mapped_column(Float)
    avg_spm: Mapped[float | None] = mapped_column(Float)

    # Heart rate
    avg_hr: Mapped[int | None] = mapped_column(Integer)
    max_hr: Mapped[int | None] = mapped_column(Integer)

    # Context
    weight_at_test: Mapped[float | None] = mapped_column(Float)  # lbs
    drag_factor: Mapped[int | None] = mapped_column(Integer)
    conditions: Mapped[str | None] = mapped_column(Text)  # fresh, fatigued, race simulation, etc.

    notes: Mapped[str | None] = mapped_column(Text)


class StepTestResult(Base):
    """Individual steps within a step test for lactate threshold estimation."""

    __tablename__ = "step_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_test_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)

    target_split_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    actual_split_seconds: Mapped[float | None] = mapped_column(Float)
    avg_hr: Mapped[int | None] = mapped_column(Integer)
    end_hr: Mapped[int | None] = mapped_column(Integer)
    spm: Mapped[float | None] = mapped_column(Float)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=240)  # typically 4 min steps
