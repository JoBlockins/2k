"""Sync Whoop data into the recovery_metrics table."""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from src.data.whoop_client import WhoopClient
from src.models.wellness import RecoveryMetrics


def sync_whoop(db: Session, days: int = 7) -> dict:
    """Pull recovery, sleep, and strain from Whoop and upsert into DB.

    Returns stats: {synced, updated, skipped, errors}.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    stats = {"synced": 0, "updated": 0, "skipped": 0, "errors": 0}

    with WhoopClient() as client:
        recoveries = client.get_recovery(start_date, end_date)
        sleeps = client.get_sleep(start_date, end_date)
        cycles = client.get_cycles(start_date, end_date)

        # Index sleep and cycle data by date for matching
        sleep_by_date = _index_by_date(sleeps)
        cycle_by_date = _index_by_date(cycles)

        for rec in recoveries:
            try:
                rec_date = datetime.fromisoformat(
                    rec.get("created_at", "").replace("Z", "+00:00")
                ).date()

                sleep = sleep_by_date.get(rec_date)
                strain = cycle_by_date.get(rec_date)
                metrics = client.parse_recovery_metrics(rec, sleep, strain)

                # Upsert — update existing or insert new
                existing = db.query(RecoveryMetrics).filter(
                    RecoveryMetrics.date == rec_date
                ).first()

                if existing:
                    if existing.source == "whoop":
                        _update_record(existing, metrics)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    db.add(metrics)
                    stats["synced"] += 1

            except Exception:
                stats["errors"] += 1

    db.commit()
    return stats


def _index_by_date(records: list[dict]) -> dict[date, dict]:
    """Build a dict mapping date -> record for fast lookup."""
    by_date: dict[date, dict] = {}
    for r in records:
        try:
            d = datetime.fromisoformat(
                r.get("created_at", "").replace("Z", "+00:00")
            ).date()
            by_date[d] = r
        except (ValueError, TypeError):
            continue
    return by_date


def _update_record(existing: RecoveryMetrics, new: RecoveryMetrics) -> None:
    """Update an existing record with new values (skip None)."""
    fields = [
        "resting_hr", "hrv_rmssd", "sleep_duration_minutes",
        "sleep_quality_score", "deep_sleep_minutes", "rem_sleep_minutes",
        "light_sleep_minutes", "awake_minutes", "whoop_recovery_score",
        "whoop_strain",
    ]
    for field in fields:
        value = getattr(new, field)
        if value is not None:
            setattr(existing, field, value)
