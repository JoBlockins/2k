"""CLI for quick workout logging without opening the dashboard.

Usage:
    python -m scripts.log_workout --type steady_state --distance 10000 --time 45 --split 2:15 --spm 20 --hr 148 --rpe 5
    python -m scripts.log_workout   # interactive mode — prompts for each field

Split format: M:SS.s (e.g., 2:15 or 1:45.3)
"""

import argparse
import re
import sys
from datetime import date

from src.data.metrics import calculate_trimp, split_to_watts
from src.models.database import SessionLocal, init_db
from src.models.workout import Workout


WORKOUT_TYPES = [
    "steady_state", "tempo", "threshold", "interval",
    "race_pace", "test", "strength", "other",
]


def parse_split(split_str: str) -> float:
    """Parse a split string like '2:15' or '1:45.3' into total seconds."""
    match = re.match(r"^(\d+):(\d{1,2}(?:\.\d+)?)$", split_str.strip())
    if not match:
        raise ValueError(
            f"Invalid split format: '{split_str}'. Use M:SS or M:SS.s (e.g., 2:15 or 1:45.3)"
        )
    minutes = int(match.group(1))
    seconds = float(match.group(2))
    if seconds >= 60:
        raise ValueError(f"Seconds must be < 60, got {seconds}")
    return minutes * 60 + seconds


def prompt_field(label: str, default=None, required: bool = False, cast=None):
    """Prompt the user for a field value. Returns None if skipped."""
    suffix = f" [{default}]" if default is not None else " (Enter to skip)"
    if required:
        suffix = f" [{default}]" if default is not None else ""

    raw = input(f"  {label}{suffix}: ").strip()

    if not raw:
        return default

    if cast:
        try:
            return cast(raw)
        except (ValueError, TypeError) as e:
            print(f"    Invalid input: {e}")
            return default
    return raw


def main():
    parser = argparse.ArgumentParser(
        description="Log a workout from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Split format: M:SS or M:SS.s (e.g., 2:15 or 1:45.3)",
    )
    parser.add_argument("--type", choices=WORKOUT_TYPES, help="Workout type")
    parser.add_argument("--distance", type=int, help="Total distance in meters")
    parser.add_argument("--time", type=float, help="Total time in minutes")
    parser.add_argument("--split", type=str, help="Average split (M:SS.s)")
    parser.add_argument("--spm", type=float, help="Average strokes per minute")
    parser.add_argument("--hr", type=int, help="Average heart rate")
    parser.add_argument("--rpe", type=int, choices=range(1, 11), help="RPE (1-10)")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD, default: today)")
    parser.add_argument("--desc", type=str, help="Description")
    parser.add_argument("--notes", type=str, help="Notes")
    args = parser.parse_args()

    # Resolve values — use args if provided, otherwise prompt interactively
    print("Log Workout")
    print("-" * 40)

    wo_type = args.type
    if not wo_type:
        print(f"  Types: {', '.join(WORKOUT_TYPES)}")
        wo_type = prompt_field("Type", default="steady_state", required=True)

    wo_date_str = args.date
    if not wo_date_str:
        wo_date_str = prompt_field("Date", default=date.today().isoformat())
    try:
        wo_date = date.fromisoformat(wo_date_str)
    except ValueError:
        print(f"Invalid date: {wo_date_str}")
        sys.exit(1)

    distance = args.distance or prompt_field("Distance (m)", cast=int)
    time_min = args.time or prompt_field("Time (minutes)", cast=float)
    time_sec = time_min * 60 if time_min else None

    split_str = args.split
    split_secs = None
    if split_str:
        split_secs = parse_split(split_str)
    else:
        raw = prompt_field("Avg split (M:SS.s)")
        if raw:
            split_secs = parse_split(raw)

    spm = args.spm or prompt_field("SPM", cast=float)
    hr = args.hr or prompt_field("Avg HR", cast=int)
    rpe = args.rpe or prompt_field("RPE (1-10)", cast=int)
    desc = args.desc or prompt_field("Description")
    notes = args.notes or prompt_field("Notes")

    # Calculate derived fields
    watts = split_to_watts(split_secs) if split_secs else None
    trimp = None
    if hr and time_sec:
        trimp = calculate_trimp(duration_minutes=time_sec / 60, avg_hr=hr)

    # Save to DB
    init_db()
    db = SessionLocal()

    workout = Workout(
        date=wo_date,
        workout_type=wo_type,
        description=desc or None,
        source="cli",
        total_distance_m=distance or None,
        total_time_seconds=time_sec,
        avg_split_seconds=split_secs,
        avg_watts=round(watts, 1) if watts else None,
        avg_spm=spm or None,
        avg_hr=hr or None,
        rpe=rpe or None,
        trimp=round(trimp, 1) if trimp else None,
        notes=notes or None,
    )

    db.add(workout)
    db.commit()
    db.close()

    # Confirm
    print()
    print("Workout saved!")
    print(f"  Date:     {wo_date}")
    print(f"  Type:     {wo_type}")
    if distance:
        print(f"  Distance: {distance:,}m")
    if time_min:
        print(f"  Time:     {time_min:.1f} min")
    if split_secs:
        mins = int(split_secs // 60)
        secs = split_secs % 60
        print(f"  Split:    {mins}:{secs:04.1f}")
    if watts:
        print(f"  Watts:    {watts:.1f}")
    if trimp:
        print(f"  TRIMP:    {trimp:.1f}")


if __name__ == "__main__":
    main()
