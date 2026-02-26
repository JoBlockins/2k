"""Concept2 Logbook CSV importer.

Handles the CSV export format from log.concept2.com season downloads.

Expected columns:
    Date, Description, Work Time (Formatted), Work Time (Seconds),
    Rest Time (Formatted), Rest Time (Seconds), Work Distance, Rest Distance,
    Stroke Rate/Cadence, Stroke Count, Pace, Avg Watts, Cal/Hour, Total Cal,
    Avg Heart Rate, Drag Factor, Age, Weight, Type, Ranked, Comments, Date Entered
"""

import csv
import os
from datetime import datetime

from sqlalchemy.orm import Session

from src.data.metrics import calculate_trimp, split_to_watts
from src.models.benchmark import BenchmarkTest
from src.models.workout import Workout

# Map distances to benchmark test types
BENCHMARK_DISTANCES = {2000: "2k", 6000: "6k", 500: "500m"}


# Map Concept2 "Type" field to our workout types
TYPE_MAP = {
    "": "general",
    "JustRow": "general",
    "FixedDistance": "general",
    "FixedTime": "steady_state",
    "FixedCalorie": "general",
    "FixedDistanceInterval": "interval",
    "FixedTimeInterval": "interval",
    "FixedCalorieInterval": "interval",
    "VariableInterval": "interval",
}


def _parse_pace(pace_str: str) -> float | None:
    """Parse a pace string like '1:45.0' or '2:00.0' into seconds."""
    if not pace_str or pace_str.strip() == "":
        return None
    pace_str = pace_str.strip()
    try:
        if ":" in pace_str:
            parts = pace_str.split(":")
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        return float(pace_str)
    except (ValueError, IndexError):
        return None


def _safe_int(value: str) -> int | None:
    if not value or value.strip() == "":
        return None
    try:
        return int(float(value.strip()))
    except ValueError:
        return None


def _safe_float(value: str) -> float | None:
    if not value or value.strip() == "":
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def import_concept2_csv(db: Session, filepath: str) -> dict:
    """
    Import workouts from a Concept2 logbook CSV export.

    Args:
        db: SQLAlchemy session
        filepath: Path to the CSV file

    Returns:
        dict with import stats (imported, skipped, errors)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    stats = {"imported": 0, "skipped": 0, "errors": 0, "error_details": []}

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # row 1 is header
            try:
                workout = _parse_row(row)
                if workout is None:
                    stats["skipped"] += 1
                    continue

                # Check for duplicate (same date + distance + time)
                existing = db.query(Workout).filter(
                    Workout.date == workout.date,
                    Workout.total_distance_m == workout.total_distance_m,
                    Workout.total_time_seconds == workout.total_time_seconds,
                    Workout.source == "concept2_csv",
                ).first()

                if existing:
                    stats["skipped"] += 1
                    continue

                # Calculate TRIMP if HR data available
                if workout.avg_hr and workout.total_time_seconds:
                    workout.trimp = calculate_trimp(
                        duration_minutes=workout.total_time_seconds / 60,
                        avg_hr=workout.avg_hr,
                    )

                db.add(workout)
                stats["imported"] += 1

                # Auto-create BenchmarkTest entry for test pieces
                if workout.workout_type == "test" and workout.total_distance_m in BENCHMARK_DISTANCES:
                    test_type = BENCHMARK_DISTANCES[workout.total_distance_m]
                    existing_bm = db.query(BenchmarkTest).filter(
                        BenchmarkTest.date == workout.date,
                        BenchmarkTest.test_type == test_type,
                    ).first()
                    if not existing_bm:
                        db.add(BenchmarkTest(
                            date=workout.date,
                            test_type=test_type,
                            total_time_seconds=workout.total_time_seconds,
                            total_distance_m=workout.total_distance_m,
                            avg_split_seconds=workout.avg_split_seconds,
                            avg_watts=workout.avg_watts,
                            avg_spm=workout.avg_spm,
                            avg_hr=workout.avg_hr,
                            drag_factor=workout.drag_factor,
                            notes=workout.notes,
                        ))

            except Exception as e:
                stats["errors"] += 1
                stats["error_details"].append(f"Row {row_num}: {str(e)}")

    db.commit()
    return stats


def _parse_row(row: dict) -> Workout | None:
    """Parse a single CSV row into a Workout model."""
    # Parse date
    date_str = row.get("Date", "").strip()
    if not date_str:
        return None

    try:
        workout_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
    except ValueError:
        try:
            workout_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                workout_date = datetime.strptime(date_str, "%m/%d/%Y").date()
            except ValueError:
                return None

    # Parse core fields
    work_time = _safe_float(row.get("Work Time (Seconds)", ""))
    work_distance = _safe_int(row.get("Work Distance", ""))

    if not work_time and not work_distance:
        return None  # skip empty rows

    # Parse pace/split
    pace_str = row.get("Pace", "")
    split_seconds = _parse_pace(pace_str)

    # Watts — use CSV value or calculate from split
    watts = _safe_float(row.get("Avg Watts", ""))
    if not watts and split_seconds:
        watts = round(split_to_watts(split_seconds), 1)

    # Workout type
    c2_type = row.get("Type", "").strip()
    workout_type = TYPE_MAP.get(c2_type, "general")

    # Classify based on distance if type is a single continuous piece (not interval)
    description = row.get("Description", "").strip()
    desc_lower = description.lower()
    is_interval = c2_type in (
        "FixedDistanceInterval", "FixedTimeInterval",
        "FixedCalorieInterval", "VariableInterval",
    ) or "x" in desc_lower.split("m")[0] or desc_lower.startswith("v")  # "8x250m", "3x2000m", "v250m/..."

    if workout_type == "general" and work_distance and not is_interval:
        if work_distance == 2000:
            workout_type = "test"
        elif work_distance == 6000:
            workout_type = "test"
        elif work_distance == 500:
            workout_type = "test"
        elif work_time and work_time >= 1800:
            workout_type = "steady_state"

    return Workout(
        date=workout_date,
        workout_type=workout_type,
        description=row.get("Description", "").strip() or None,
        source="concept2_csv",
        total_distance_m=work_distance,
        total_time_seconds=work_time,
        avg_split_seconds=split_seconds,
        avg_watts=round(watts, 1) if watts else None,
        avg_spm=_safe_float(row.get("Stroke Rate/Cadence", "")),
        avg_hr=_safe_int(row.get("Avg Heart Rate", "")),
        drag_factor=_safe_int(row.get("Drag Factor", "")),
        notes=row.get("Comments", "").strip() or None,
    )


def import_from_directory(db: Session, dirpath: str) -> dict:
    """Import all CSV files from a directory."""
    total_stats = {"imported": 0, "skipped": 0, "errors": 0, "files": 0, "error_details": []}

    for filename in sorted(os.listdir(dirpath)):
        if filename.lower().endswith(".csv"):
            filepath = os.path.join(dirpath, filename)
            stats = import_concept2_csv(db, filepath)
            total_stats["imported"] += stats["imported"]
            total_stats["skipped"] += stats["skipped"]
            total_stats["errors"] += stats["errors"]
            total_stats["error_details"].extend(stats["error_details"])
            total_stats["files"] += 1
            print(f"  {filename}: {stats['imported']} imported, {stats['skipped']} skipped, {stats['errors']} errors")

    return total_stats
