"""Sync Wyze scale data into the body_weight table."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from src.data.wyze_client import WyzeScaleClient
from src.models.body import BodyWeight


def sync_wyze(db: Session, days: int = 7) -> dict:
    """Pull weight and body composition from Wyze and upsert into DB.

    Returns stats: {synced, updated, skipped, errors}.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    stats = {"synced": 0, "updated": 0, "skipped": 0, "errors": 0}

    with WyzeScaleClient() as client:
        records = client.get_weight_records(start_date, end_date)

        for record in records:
            try:
                existing = db.query(BodyWeight).filter(
                    BodyWeight.date == record.date
                ).first()

                if existing:
                    if existing.source == "wyze":
                        _update_record(existing, record)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    db.add(record)
                    stats["synced"] += 1

            except Exception:
                stats["errors"] += 1

    db.commit()
    return stats


def _update_record(existing: BodyWeight, new: BodyWeight) -> None:
    """Update an existing record with new values (skip None)."""
    fields = ["weight_lbs", "body_fat_pct", "muscle_mass_lbs", "water_pct"]
    for field in fields:
        value = getattr(new, field)
        if value is not None:
            setattr(existing, field, value)
