"""Training plan and scheduled workout models."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class TrainingPhase(Base):
    """A macrocycle training phase (e.g., Base 1, Build, Peak)."""

    __tablename__ = "training_phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # base_1, base_2, build, peak
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    focus: Mapped[str | None] = mapped_column(Text)  # primary training focus
    target_weekly_volume_m: Mapped[int | None] = mapped_column(Integer)  # target meters/week
    target_intensity_split: Mapped[str | None] = mapped_column(String(10))  # e.g. "80/20"
    notes: Mapped[str | None] = mapped_column(Text)


class PlannedWorkout(Base):
    """A workout scheduled in the training plan."""

    __tablename__ = "planned_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase_id: Mapped[int | None] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Workout specification
    workout_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # steady_state, tempo, threshold, interval, race_pace, test, strength, rest
    title: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g. "60min Steady State"
    description: Mapped[str | None] = mapped_column(Text)  # detailed prescription

    # Targets
    target_distance_m: Mapped[int | None] = mapped_column(Integer)
    target_time_seconds: Mapped[float | None] = mapped_column(Float)
    target_split_seconds: Mapped[float | None] = mapped_column(Float)
    target_spm_low: Mapped[int | None] = mapped_column(Integer)
    target_spm_high: Mapped[int | None] = mapped_column(Integer)
    target_hr_low: Mapped[int | None] = mapped_column(Integer)
    target_hr_high: Mapped[int | None] = mapped_column(Integer)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    # scheduled, completed, skipped, modified
    completed_workout_id: Mapped[int | None] = mapped_column(Integer)  # FK to workouts.id

    # AI adjustment tracking
    was_adjusted: Mapped[bool | None] = mapped_column(Integer, default=False)
    adjustment_reason: Mapped[str | None] = mapped_column(Text)


class WeeklyPlan(Base):
    """Weekly training plan summary."""

    __tablename__ = "weekly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    phase_id: Mapped[int | None] = mapped_column(Integer)

    target_volume_m: Mapped[int | None] = mapped_column(Integer)
    target_sessions: Mapped[int | None] = mapped_column(Integer)
    focus: Mapped[str | None] = mapped_column(Text)
    ai_notes: Mapped[str | None] = mapped_column(Text)  # AI-generated plan rationale
