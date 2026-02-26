"""Training plan generator — creates periodized training plans with specific workouts."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from src.data.metrics import format_split, watts_to_split
from src.models.training_plan import PlannedWorkout, TrainingPhase, WeeklyPlan

# ──────────────────────────────────────────────
# Workout templates
# ──────────────────────────────────────────────

# Splits are in seconds per 500m. These are parameterized by current fitness.
WORKOUT_TEMPLATES = {
    # Steady state workouts (UT2/UT1)
    "ss_60min": {
        "title": "60min Steady State",
        "workout_type": "steady_state",
        "description": "60 minutes at UT2 pace. Focus on long, relaxed strokes. HR 137-156.",
        "target_time_seconds": 3600,
        "spm_range": (18, 22),
        "hr_range": (137, 156),
        "split_offset": 15,  # seconds above 2k split
    },
    "ss_90min": {
        "title": "90min Steady State",
        "workout_type": "steady_state",
        "description": "90 minutes at easy UT2 pace. Building aerobic base. HR 130-150.",
        "target_time_seconds": 5400,
        "spm_range": (18, 20),
        "hr_range": (130, 150),
        "split_offset": 18,
    },
    "ss_2x30min": {
        "title": "2x30min Steady State (2:00 rest)",
        "workout_type": "steady_state",
        "description": "Two 30-minute pieces with 2 minutes rest. UT1 pace. HR 145-156.",
        "target_time_seconds": 3720,
        "spm_range": (20, 24),
        "hr_range": (145, 156),
        "split_offset": 13,
    },
    # Tempo / AT workouts
    "tempo_3x20min": {
        "title": "3x20min Tempo (3:00 rest)",
        "workout_type": "tempo",
        "description": "Three 20-minute pieces at AT pace. HR 156-166. Building lactate clearance.",
        "target_time_seconds": 3960,
        "spm_range": (22, 26),
        "hr_range": (156, 166),
        "split_offset": 8,
    },
    "tempo_4x15min": {
        "title": "4x15min Tempo (2:00 rest)",
        "workout_type": "tempo",
        "description": "Four 15-minute pieces at AT pace. HR 156-166.",
        "target_time_seconds": 3960,
        "spm_range": (22, 26),
        "hr_range": (156, 166),
        "split_offset": 8,
    },
    # Threshold intervals
    "threshold_6x1k": {
        "title": "6x1000m (3:00 rest)",
        "workout_type": "threshold",
        "description": "Six 1k reps at threshold pace. Target 2k split + 2-3 seconds.",
        "target_distance_m": 6000,
        "spm_range": (26, 30),
        "hr_range": (166, 179),
        "split_offset": 3,
    },
    "threshold_4x2k": {
        "title": "4x2000m (4:00 rest)",
        "workout_type": "threshold",
        "description": "Four 2k reps at threshold pace. Target 2k split + 3-5 seconds.",
        "target_distance_m": 8000,
        "spm_range": (26, 30),
        "hr_range": (166, 179),
        "split_offset": 4,
    },
    "threshold_8x500m": {
        "title": "8x500m (2:00 rest)",
        "workout_type": "interval",
        "description": "Eight 500m reps near race pace. Target 2k split - 1 to + 1.",
        "target_distance_m": 4000,
        "spm_range": (28, 34),
        "hr_range": (170, 185),
        "split_offset": 0,
    },
    # Race pace
    "race_4x1k": {
        "title": "4x1000m Race Pace (5:00 rest)",
        "workout_type": "race_pace",
        "description": "Four 1k reps at goal 2k pace. Practice target split.",
        "target_distance_m": 4000,
        "spm_range": (30, 34),
        "hr_range": (175, 190),
        "split_offset": 0,  # at goal pace
        "use_goal_split": True,
    },
    # Strength
    "strength_rowing": {
        "title": "Rowing Strength Session",
        "workout_type": "strength",
        "description": "Deadlift 5x5, Back Squat 4x6, Bench Pull 4x8, Core circuit. Focus on rowing-specific power.",
        "target_time_seconds": 3600,
    },
    # Rest
    "rest_day": {
        "title": "Rest Day",
        "workout_type": "rest",
        "description": "Full rest. Light stretching or walking only.",
    },
}

# ──────────────────────────────────────────────
# Weekly templates by phase
# ──────────────────────────────────────────────

WEEKLY_TEMPLATES = {
    "base_1": {
        "focus": "Aerobic foundation — high volume, low intensity",
        "sessions": [
            "ss_60min",     # Monday
            "ss_90min",     # Tuesday
            "strength_rowing",  # Wednesday AM
            "ss_60min",     # Wednesday PM
            "ss_2x30min",   # Thursday
            "ss_60min",     # Friday
            "ss_90min",     # Saturday
            "rest_day",     # Sunday
        ],
        "target_volume_m": 80000,
    },
    "base_2": {
        "focus": "Build aerobic capacity, introduce tempo work",
        "sessions": [
            "ss_60min",     # Monday
            "tempo_3x20min",  # Tuesday
            "strength_rowing",  # Wednesday AM
            "ss_60min",     # Wednesday PM
            "ss_2x30min",   # Thursday
            "tempo_4x15min",  # Friday
            "ss_90min",     # Saturday
            "rest_day",     # Sunday
        ],
        "target_volume_m": 90000,
    },
    "build": {
        "focus": "Threshold and race-pace development",
        "sessions": [
            "ss_60min",     # Monday
            "threshold_4x2k",  # Tuesday
            "strength_rowing",  # Wednesday AM
            "ss_60min",     # Wednesday PM
            "threshold_6x1k",  # Thursday
            "ss_2x30min",   # Friday
            "threshold_8x500m",  # Saturday
            "rest_day",     # Sunday
        ],
        "target_volume_m": 70000,
    },
    "peak": {
        "focus": "Sharpen race fitness, reduce volume",
        "sessions": [
            "ss_60min",     # Monday
            "race_4x1k",   # Tuesday
            "rest_day",     # Wednesday
            "threshold_8x500m",  # Thursday
            "ss_60min",     # Friday
            "rest_day",     # Saturday
            "rest_day",     # Sunday
        ],
        "target_volume_m": 40000,
    },
}


# ──────────────────────────────────────────────
# Plan generator
# ──────────────────────────────────────────────

def create_training_phases(db: Session) -> list[TrainingPhase]:
    """Create the macro-level training phases for Feb-Aug 2026."""
    phases = [
        TrainingPhase(
            name="base_1",
            start_date=date(2026, 2, 9),
            end_date=date(2026, 3, 29),
            focus="Aerobic foundation. Build steady state volume to 70-90k meters/week.",
            target_weekly_volume_m=80000,
            target_intensity_split="80/20",
        ),
        TrainingPhase(
            name="base_2",
            start_date=date(2026, 3, 30),
            end_date=date(2026, 5, 24),
            focus="Build aerobic capacity. Introduce tempo work. 80-100k meters/week.",
            target_weekly_volume_m=90000,
            target_intensity_split="75/25",
        ),
        TrainingPhase(
            name="build",
            start_date=date(2026, 5, 25),
            end_date=date(2026, 7, 19),
            focus="Threshold and race-pace intervals. 60-80k meters/week.",
            target_weekly_volume_m=70000,
            target_intensity_split="70/30",
        ),
        TrainingPhase(
            name="peak",
            start_date=date(2026, 7, 20),
            end_date=date(2026, 8, 9),
            focus="Sharpen race fitness. Taper volume. Race simulations.",
            target_weekly_volume_m=40000,
            target_intensity_split="60/40",
        ),
    ]

    for phase in phases:
        db.add(phase)
    db.commit()

    for phase in phases:
        db.refresh(phase)

    return phases


def generate_weekly_plan(
    db: Session,
    week_start: date,
    phase: TrainingPhase,
    current_2k_split: float = 102.5,  # 1:42.5 default
    goal_2k_split: float = 97.5,  # 1:37.5 goal
) -> list[PlannedWorkout]:
    """Generate a week of workouts based on the training phase and current fitness."""
    template = WEEKLY_TEMPLATES.get(phase.name)
    if not template:
        return []

    # Create weekly plan record
    weekly = WeeklyPlan(
        week_start=week_start,
        phase_id=phase.id,
        target_volume_m=template["target_volume_m"],
        target_sessions=len([s for s in template["sessions"] if s != "rest_day"]),
        focus=template["focus"],
    )
    db.add(weekly)

    workouts = []
    for day_offset, session_key in enumerate(template["sessions"]):
        workout_template = WORKOUT_TEMPLATES[session_key]
        workout_date = week_start + timedelta(days=day_offset)

        # Calculate target split based on current fitness
        target_split = None
        if "split_offset" in workout_template:
            if workout_template.get("use_goal_split"):
                target_split = goal_2k_split
            else:
                target_split = current_2k_split + workout_template["split_offset"]

        spm_low, spm_high = workout_template.get("spm_range", (None, None))
        hr_low, hr_high = workout_template.get("hr_range", (None, None))

        # Build description with specific targets
        desc = workout_template["description"]
        if target_split:
            desc += f"\nTarget split: {format_split(target_split)}"

        planned = PlannedWorkout(
            phase_id=phase.id,
            date=workout_date,
            workout_type=workout_template["workout_type"],
            title=workout_template["title"],
            description=desc,
            target_distance_m=workout_template.get("target_distance_m"),
            target_time_seconds=workout_template.get("target_time_seconds"),
            target_split_seconds=target_split,
            target_spm_low=spm_low,
            target_spm_high=spm_high,
            target_hr_low=hr_low,
            target_hr_high=hr_high,
            status="scheduled",
        )
        workouts.append(planned)
        db.add(planned)

    db.commit()
    return workouts


def generate_full_plan(db: Session) -> dict:
    """Generate the complete training plan from current date through peak phase."""
    phases = create_training_phases(db)
    total_workouts = 0

    for phase in phases:
        current = phase.start_date
        # Align to Monday
        days_to_monday = (7 - current.weekday()) % 7
        if days_to_monday > 0:
            current += timedelta(days=days_to_monday)
        if current < phase.start_date:
            current = phase.start_date

        while current <= phase.end_date:
            workouts = generate_weekly_plan(db, current, phase)
            total_workouts += len(workouts)
            current += timedelta(days=7)

    return {
        "phases": len(phases),
        "total_workouts": total_workouts,
        "start_date": phases[0].start_date.isoformat(),
        "end_date": phases[-1].end_date.isoformat(),
    }
