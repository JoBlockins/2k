"""Body weight and composition data models (Tier 4)."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.database import Base


class BodyWeight(Base):
    """Daily body weight measurements."""

    __tablename__ = "body_weight"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    weight_lbs: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual, withings

    # Withings extras
    body_fat_pct: Mapped[float | None] = mapped_column(Float)
    muscle_mass_lbs: Mapped[float | None] = mapped_column(Float)
    water_pct: Mapped[float | None] = mapped_column(Float)
