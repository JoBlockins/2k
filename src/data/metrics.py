"""Derived metrics engine — calculates training load, fitness/fatigue, zone distributions, and 2k predictions."""

import math
from datetime import date, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.data.config import Config
from src.models.benchmark import BenchmarkTest
from src.models.body import BodyWeight
from src.models.wellness import RecoveryMetrics
from src.models.workout import Workout


# ──────────────────────────────────────────────
# Rowing physics
# ──────────────────────────────────────────────

def split_to_watts(split_seconds: float) -> float:
    """Convert 500m split (seconds) to watts. Concept2 formula: P = 2.80 / pace^3."""
    pace = split_seconds / 500.0  # seconds per meter
    return 2.80 / (pace ** 3)


def watts_to_split(watts: float) -> float:
    """Convert watts to 500m split (seconds)."""
    if watts <= 0:
        return 0
    pace = (2.80 / watts) ** (1 / 3)  # seconds per meter
    return pace * 500


def format_split(seconds: float) -> str:
    """Format split seconds as M:SS.t (e.g., 1:45.0)."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:04.1f}"


def format_time(seconds: float) -> str:
    """Format total time as M:SS or H:MM:SS."""
    if seconds >= 3600:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:04.1f}"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:04.1f}"


# ──────────────────────────────────────────────
# Training zones (rowing-specific)
# ──────────────────────────────────────────────

# Zone definitions based on % of max HR
ZONE_DEFINITIONS = {
    "UT2": {"name": "Utilization 2 (Easy)", "hr_pct_low": 0.55, "hr_pct_high": 0.70},
    "UT1": {"name": "Utilization 1 (Steady State)", "hr_pct_low": 0.70, "hr_pct_high": 0.80},
    "AT": {"name": "Anaerobic Threshold", "hr_pct_low": 0.80, "hr_pct_high": 0.85},
    "TR": {"name": "Transport (VO2max)", "hr_pct_low": 0.85, "hr_pct_high": 0.92},
    "AN": {"name": "Anaerobic", "hr_pct_low": 0.92, "hr_pct_high": 1.00},
}


def get_hr_zones(max_hr: int | None = None) -> dict[str, tuple[int, int]]:
    """Calculate HR zone boundaries."""
    max_hr = max_hr or Config.ATHLETE_MAX_HR
    zones = {}
    for zone_key, zone_def in ZONE_DEFINITIONS.items():
        zones[zone_key] = (
            int(max_hr * zone_def["hr_pct_low"]),
            int(max_hr * zone_def["hr_pct_high"]),
        )
    return zones


def classify_hr_zone(hr: int, max_hr: int | None = None) -> str:
    """Classify a heart rate into a training zone."""
    zones = get_hr_zones(max_hr)
    for zone_key in ["AN", "TR", "AT", "UT1", "UT2"]:  # check highest first
        low, high = zones[zone_key]
        if hr >= low:
            return zone_key
    return "UT2"  # below UT2 is still UT2


# ──────────────────────────────────────────────
# Training load (TRIMP)
# ──────────────────────────────────────────────

def calculate_trimp(duration_minutes: float, avg_hr: int,
                    resting_hr: int | None = None, max_hr: int | None = None,
                    sex: str = "male") -> float:
    """
    Calculate Banister TRIMP (Training Impulse).
    TRIMP = duration * HR_ratio * 0.64 * e^(1.92 * HR_ratio) for males
    where HR_ratio = (avg_HR - resting_HR) / (max_HR - resting_HR)
    """
    resting_hr = resting_hr or Config.ATHLETE_RESTING_HR
    max_hr = max_hr or Config.ATHLETE_MAX_HR

    if max_hr <= resting_hr or avg_hr <= resting_hr:
        return 0

    hr_ratio = (avg_hr - resting_hr) / (max_hr - resting_hr)
    hr_ratio = max(0, min(1, hr_ratio))

    if sex == "male":
        return duration_minutes * hr_ratio * 0.64 * math.exp(1.92 * hr_ratio)
    else:
        return duration_minutes * hr_ratio * 0.86 * math.exp(1.67 * hr_ratio)


# ──────────────────────────────────────────────
# Fitness / Fatigue model (Banister)
# ──────────────────────────────────────────────

def calculate_fitness_fatigue(db: Session, as_of: date) -> dict:
    """
    Calculate CTL (Chronic Training Load / Fitness) and ATL (Acute Training Load / Fatigue)
    using exponentially weighted moving averages of daily TRIMP.

    CTL = 42-day EWMA (fitness)
    ATL = 7-day EWMA (fatigue)
    TSB = CTL - ATL (form / freshness)
    """
    lookback = 60  # days of data to consider
    start = as_of - timedelta(days=lookback)

    workouts = db.query(Workout).filter(
        and_(Workout.date >= start, Workout.date <= as_of)
    ).order_by(Workout.date).all()

    # Build daily TRIMP map
    daily_trimp: dict[date, float] = {}
    for w in workouts:
        if w.trimp:
            daily_trimp[w.date] = daily_trimp.get(w.date, 0) + w.trimp

    # Calculate EWMA
    ctl = 0.0  # Chronic (42-day)
    atl = 0.0  # Acute (7-day)
    ctl_decay = 1 / 42
    atl_decay = 1 / 7

    current = start
    while current <= as_of:
        trimp = daily_trimp.get(current, 0)
        ctl = ctl + ctl_decay * (trimp - ctl)
        atl = atl + atl_decay * (trimp - atl)
        current += timedelta(days=1)

    tsb = ctl - atl  # Training Stress Balance (form)

    return {
        "ctl": round(ctl, 1),
        "atl": round(atl, 1),
        "tsb": round(tsb, 1),
        "status": _interpret_tsb(tsb),
    }


def _interpret_tsb(tsb: float) -> str:
    """Interpret Training Stress Balance."""
    if tsb > 25:
        return "very_fresh"
    elif tsb > 10:
        return "fresh"
    elif tsb > -10:
        return "neutral"
    elif tsb > -25:
        return "fatigued"
    else:
        return "very_fatigued"


# ──────────────────────────────────────────────
# Acute:Chronic Workload Ratio (injury risk)
# ──────────────────────────────────────────────

def calculate_acwr(db: Session, as_of: date) -> dict:
    """
    Acute:Chronic Workload Ratio.
    Acute = 7-day total training load
    Chronic = 28-day average weekly training load
    Ratio 0.8-1.3 = "sweet spot", >1.5 = danger zone
    """
    acute_start = as_of - timedelta(days=6)
    chronic_start = as_of - timedelta(days=27)

    workouts = db.query(Workout).filter(
        and_(Workout.date >= chronic_start, Workout.date <= as_of)
    ).all()

    acute_load = sum(w.trimp or 0 for w in workouts if w.date >= acute_start)
    chronic_load = sum(w.trimp or 0 for w in workouts)
    chronic_weekly = chronic_load / 4  # 4-week average

    if chronic_weekly == 0:
        return {"acwr": 0, "acute": acute_load, "chronic_weekly": 0, "risk": "insufficient_data"}

    acwr = acute_load / chronic_weekly

    if acwr < 0.8:
        risk = "undertraining"
    elif acwr <= 1.3:
        risk = "optimal"
    elif acwr <= 1.5:
        risk = "caution"
    else:
        risk = "high_risk"

    return {
        "acwr": round(acwr, 2),
        "acute": round(acute_load, 1),
        "chronic_weekly": round(chronic_weekly, 1),
        "risk": risk,
    }


# ──────────────────────────────────────────────
# Weekly volume and zone distribution
# ──────────────────────────────────────────────

def weekly_summary(db: Session, week_start: date) -> dict:
    """Calculate weekly training summary."""
    week_end = week_start + timedelta(days=6)

    workouts = db.query(Workout).filter(
        and_(Workout.date >= week_start, Workout.date <= week_end)
    ).all()

    total_meters = sum(w.total_distance_m or 0 for w in workouts)
    total_time = sum(w.total_time_seconds or 0 for w in workouts)
    total_trimp = sum(w.trimp or 0 for w in workouts)
    session_count = len(workouts)

    # Zone distribution
    zone_time = {
        "zone_1": sum(w.time_in_zone_1_seconds or 0 for w in workouts),
        "zone_2": sum(w.time_in_zone_2_seconds or 0 for w in workouts),
        "zone_3": sum(w.time_in_zone_3_seconds or 0 for w in workouts),
        "zone_4": sum(w.time_in_zone_4_seconds or 0 for w in workouts),
        "zone_5": sum(w.time_in_zone_5_seconds or 0 for w in workouts),
    }

    low_intensity = zone_time["zone_1"] + zone_time["zone_2"]
    high_intensity = zone_time["zone_3"] + zone_time["zone_4"] + zone_time["zone_5"]
    total_zone_time = low_intensity + high_intensity

    return {
        "week_start": week_start.isoformat(),
        "total_meters": total_meters,
        "total_time_seconds": round(total_time, 1),
        "total_trimp": round(total_trimp, 1),
        "session_count": session_count,
        "low_intensity_pct": round(low_intensity / total_zone_time * 100, 1) if total_zone_time > 0 else None,
        "high_intensity_pct": round(high_intensity / total_zone_time * 100, 1) if total_zone_time > 0 else None,
        "zone_time": zone_time,
    }


# ──────────────────────────────────────────────
# 2k prediction
# ──────────────────────────────────────────────

def predict_2k_from_6k(six_k_split_seconds: float) -> float:
    """
    Predict 2k split from 6k split.
    Empirical relationship: 2k split ≈ 6k split - 5 to 7 seconds.
    Using 6 seconds as middle estimate.
    """
    return six_k_split_seconds - 6.0


def predict_2k_from_30min(distance_m: int) -> float:
    """
    Predict 2k time from 30-minute test distance.
    30min pace ≈ 6k pace. Use similar relationship.
    """
    thirty_min_split = (30 * 60 / distance_m) * 500  # seconds per 500m
    predicted_2k_split = thirty_min_split - 6.0
    return predicted_2k_split * 4  # total time for 2k (4 x 500m)


def predict_2k_from_benchmarks(db: Session) -> dict | None:
    """
    Predict current 2k ability from most recent benchmark tests.
    Uses weighted combination of available test results.
    """
    predictions = []

    # Most recent 6k
    latest_6k = db.query(BenchmarkTest).filter(
        BenchmarkTest.test_type == "6k"
    ).order_by(BenchmarkTest.date.desc()).first()

    if latest_6k and latest_6k.avg_split_seconds:
        pred_split = predict_2k_from_6k(latest_6k.avg_split_seconds)
        predictions.append({
            "source": "6k_test",
            "date": latest_6k.date.isoformat(),
            "predicted_2k_split": pred_split,
            "predicted_2k_time": pred_split * 4,
            "confidence": 0.85,
        })

    # Most recent 30min
    latest_30min = db.query(BenchmarkTest).filter(
        BenchmarkTest.test_type == "30min"
    ).order_by(BenchmarkTest.date.desc()).first()

    if latest_30min and latest_30min.total_distance_m:
        pred_time = predict_2k_from_30min(latest_30min.total_distance_m)
        predictions.append({
            "source": "30min_test",
            "date": latest_30min.date.isoformat(),
            "predicted_2k_split": pred_time / 4,
            "predicted_2k_time": pred_time,
            "confidence": 0.80,
        })

    # Most recent actual 2k
    latest_2k = db.query(BenchmarkTest).filter(
        BenchmarkTest.test_type == "2k"
    ).order_by(BenchmarkTest.date.desc()).first()

    if latest_2k and latest_2k.total_time_seconds:
        predictions.append({
            "source": "actual_2k",
            "date": latest_2k.date.isoformat(),
            "predicted_2k_split": latest_2k.avg_split_seconds,
            "predicted_2k_time": latest_2k.total_time_seconds,
            "confidence": 1.0,
        })

    if not predictions:
        return None

    # Weighted average prediction
    total_weight = sum(p["confidence"] for p in predictions)
    weighted_time = sum(p["predicted_2k_time"] * p["confidence"] for p in predictions) / total_weight

    return {
        "predicted_2k_time": round(weighted_time, 1),
        "predicted_2k_split": round(weighted_time / 4, 1),
        "formatted_time": format_time(weighted_time),
        "formatted_split": format_split(weighted_time / 4),
        "goal_time": Config.GOAL_2K_SECONDS,
        "gap_seconds": round(weighted_time - Config.GOAL_2K_SECONDS, 1),
        "predictions": predictions,
    }


# ──────────────────────────────────────────────
# Weight tracking
# ──────────────────────────────────────────────

def weight_trend(db: Session, as_of: date) -> dict | None:
    """Calculate 7-day rolling average weight and trend."""
    start = as_of - timedelta(days=13)  # need 2 weeks for trend

    weights = db.query(BodyWeight).filter(
        and_(BodyWeight.date >= start, BodyWeight.date <= as_of)
    ).order_by(BodyWeight.date).all()

    if not weights:
        return None

    recent_7 = [w.weight_lbs for w in weights if w.date > as_of - timedelta(days=7)]
    prior_7 = [w.weight_lbs for w in weights if w.date <= as_of - timedelta(days=7)]

    current_avg = sum(recent_7) / len(recent_7) if recent_7 else None
    prior_avg = sum(prior_7) / len(prior_7) if prior_7 else None

    latest = weights[-1].weight_lbs

    trend = None
    if current_avg and prior_avg:
        trend = round(current_avg - prior_avg, 1)

    target = Config.ATHLETE_WEIGHT_LBS
    deviation = round(latest - target, 1) if latest else None

    status = "on_target"
    if deviation and abs(deviation) > 2:
        status = "over" if deviation > 0 else "under"
    elif deviation and abs(deviation) > 1:
        status = "slightly_over" if deviation > 0 else "slightly_under"

    return {
        "latest": latest,
        "seven_day_avg": round(current_avg, 1) if current_avg else None,
        "trend": trend,
        "deviation_from_target": deviation,
        "status": status,
        "target": target,
    }
