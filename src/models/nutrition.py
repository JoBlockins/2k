"""Nutrition and hydration data models (Tier 6)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class DailyNutrition(Base):
    """Daily nutrition summary."""

    __tablename__ = "daily_nutrition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    calories: Mapped[int | None] = mapped_column(Integer)
    protein_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    fat_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)
    hydration_oz: Mapped[float | None] = mapped_column(Float)

    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual, myfitnesspal
