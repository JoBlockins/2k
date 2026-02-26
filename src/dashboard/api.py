"""FastAPI backend API for the training dashboard."""

from datetime import date, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.agent.coach import CoachAgent
from src.agent.plan_generator import generate_full_plan, generate_weekly_plan
from src.data.concept2_csv import import_concept2_csv
from src.data.whoop_client import WhoopAuthError
from src.data.whoop_sync import sync_whoop
from src.data.metrics import (
    calculate_acwr,
    calculate_fitness_fatigue,
    calculate_trimp,
    format_split,
    format_time,
    predict_2k_from_benchmarks,
    weekly_summary,
    weight_trend,
)
from src.models.benchmark import BenchmarkTest
from src.models.body import BodyWeight
from src.models.database import get_db, init_db
from src.models.nutrition import DailyNutrition
from src.models.strength import StrengthBenchmark, StrengthExercise, StrengthSession
from src.models.training_plan import PlannedWorkout, TrainingPhase
from src.models.wellness import DailyWellness, RecoveryMetrics
from src.models.workout import Workout, WorkoutInterval

app = FastAPI(title="2K Training Coach", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()


# ── Pydantic schemas ──────────────────────────


class WorkoutCreate(BaseModel):
    date: date
    workout_type: str
    description: Optional[str] = None
    total_distance_m: Optional[int] = None
    total_time_seconds: Optional[float] = None
    avg_split_seconds: Optional[float] = None
    avg_watts: Optional[float] = None
    avg_spm: Optional[float] = None
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    rpe: Optional[int] = Field(None, ge=1, le=10)
    drag_factor: Optional[int] = None
    notes: Optional[str] = None


class WellnessCreate(BaseModel):
    date: date
    fatigue: Optional[int] = Field(None, ge=1, le=10)
    muscle_soreness: Optional[int] = Field(None, ge=1, le=10)
    stress: Optional[int] = Field(None, ge=1, le=10)
    mood: Optional[int] = Field(None, ge=1, le=10)
    sleep_quality_subjective: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class WeightCreate(BaseModel):
    date: date
    weight_lbs: float
    body_fat_pct: Optional[float] = None


class NutritionCreate(BaseModel):
    date: date
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    hydration_oz: Optional[float] = None


class BenchmarkCreate(BaseModel):
    date: date
    test_type: str  # 2k, 6k, 30min, 500m, step
    total_time_seconds: Optional[float] = None
    total_distance_m: Optional[int] = None
    avg_split_seconds: Optional[float] = None
    avg_watts: Optional[float] = None
    avg_spm: Optional[float] = None
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    weight_at_test: Optional[float] = None
    drag_factor: Optional[int] = None
    notes: Optional[str] = None


class StrengthBenchmarkCreate(BaseModel):
    date: date
    exercise_name: str
    test_type: str  # 1rm, 3rm, 5rm
    weight_lbs: float
    bodyweight_lbs: Optional[float] = None


class ChatRequest(BaseModel):
    question: str


# ── Workout endpoints ──────────────────────────


@app.post("/api/workouts")
def create_workout(data: WorkoutCreate, db: Session = Depends(get_db)):
    workout = Workout(**data.model_dump(), source="manual")

    # Calculate TRIMP if HR data available
    if workout.avg_hr and workout.total_time_seconds:
        workout.trimp = calculate_trimp(
            duration_minutes=workout.total_time_seconds / 60,
            avg_hr=workout.avg_hr,
        )

    db.add(workout)
    db.commit()
    db.refresh(workout)
    return {"id": workout.id, "trimp": workout.trimp}


@app.get("/api/workouts")
def list_workouts(
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Workout).order_by(Workout.date.desc())
    if start:
        query = query.filter(Workout.date >= start)
    if end:
        query = query.filter(Workout.date <= end)
    workouts = query.limit(limit).all()

    return [
        {
            "id": w.id,
            "date": w.date.isoformat(),
            "workout_type": w.workout_type,
            "description": w.description,
            "total_distance_m": w.total_distance_m,
            "total_time_seconds": w.total_time_seconds,
            "avg_split": format_split(w.avg_split_seconds) if w.avg_split_seconds else None,
            "avg_split_seconds": w.avg_split_seconds,
            "avg_watts": w.avg_watts,
            "avg_spm": w.avg_spm,
            "avg_hr": w.avg_hr,
            "rpe": w.rpe,
            "trimp": w.trimp,
        }
        for w in workouts
    ]


# ── Wellness endpoints ──────────────────────────


@app.post("/api/wellness")
def create_wellness(data: WellnessCreate, db: Session = Depends(get_db)):
    # Upsert — replace if exists for same date
    existing = db.query(DailyWellness).filter(DailyWellness.date == data.date).first()
    if existing:
        for key, value in data.model_dump().items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        return {"id": existing.id, "updated": True}

    wellness = DailyWellness(**data.model_dump())
    db.add(wellness)
    db.commit()
    db.refresh(wellness)
    return {"id": wellness.id, "updated": False}


@app.get("/api/wellness")
def list_wellness(days: int = 14, db: Session = Depends(get_db)):
    start = date.today() - timedelta(days=days)
    records = db.query(DailyWellness).filter(
        DailyWellness.date >= start
    ).order_by(DailyWellness.date.desc()).all()

    return [
        {
            "date": w.date.isoformat(),
            "fatigue": w.fatigue,
            "muscle_soreness": w.muscle_soreness,
            "stress": w.stress,
            "mood": w.mood,
            "sleep_quality_subjective": w.sleep_quality_subjective,
        }
        for w in records
    ]


# ── Weight endpoints ──────────────────────────


@app.post("/api/weight")
def create_weight(data: WeightCreate, db: Session = Depends(get_db)):
    weight = BodyWeight(**data.model_dump(), source="manual")
    db.add(weight)
    db.commit()
    db.refresh(weight)
    return {"id": weight.id}


@app.get("/api/weight/trend")
def get_weight_trend(db: Session = Depends(get_db)):
    trend = weight_trend(db, date.today())
    if not trend:
        raise HTTPException(404, "No weight data available")
    return trend


# ── Nutrition endpoints ──────────────────────────


@app.post("/api/nutrition")
def create_nutrition(data: NutritionCreate, db: Session = Depends(get_db)):
    existing = db.query(DailyNutrition).filter(DailyNutrition.date == data.date).first()
    if existing:
        for key, value in data.model_dump().items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        return {"id": existing.id, "updated": True}

    nutrition = DailyNutrition(**data.model_dump())
    db.add(nutrition)
    db.commit()
    db.refresh(nutrition)
    return {"id": nutrition.id, "updated": False}


# ── Benchmark endpoints ──────────────────────────


@app.post("/api/benchmarks")
def create_benchmark(data: BenchmarkCreate, db: Session = Depends(get_db)):
    benchmark = BenchmarkTest(**data.model_dump())
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return {"id": benchmark.id}


@app.get("/api/benchmarks")
def list_benchmarks(test_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(BenchmarkTest).order_by(BenchmarkTest.date.desc())
    if test_type:
        query = query.filter(BenchmarkTest.test_type == test_type)
    tests = query.all()

    return [
        {
            "id": t.id,
            "date": t.date.isoformat(),
            "test_type": t.test_type,
            "total_time": format_time(t.total_time_seconds) if t.total_time_seconds else None,
            "total_time_seconds": t.total_time_seconds,
            "total_distance_m": t.total_distance_m,
            "avg_split": format_split(t.avg_split_seconds) if t.avg_split_seconds else None,
            "avg_split_seconds": t.avg_split_seconds,
            "avg_watts": t.avg_watts,
        }
        for t in tests
    ]


# ── Strength endpoints ──────────────────────────


@app.post("/api/strength/benchmarks")
def create_strength_benchmark(data: StrengthBenchmarkCreate, db: Session = Depends(get_db)):
    benchmark = StrengthBenchmark(**data.model_dump())
    if benchmark.bodyweight_lbs and benchmark.bodyweight_lbs > 0:
        benchmark.bw_ratio = round(benchmark.weight_lbs / benchmark.bodyweight_lbs, 2)
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return {"id": benchmark.id, "bw_ratio": benchmark.bw_ratio}


# ── Concept2 CSV import ──────────────────────────


@app.post("/api/import/concept2-csv")
def import_concept2(filepath: str, db: Session = Depends(get_db)):
    try:
        stats = import_concept2_csv(db, filepath)
        return stats
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))


# ── Whoop sync ──────────────────────────


@app.post("/api/sync/whoop")
def sync_whoop_data(days: int = 7, db: Session = Depends(get_db)):
    try:
        stats = sync_whoop(db, days=days)
        return stats
    except WhoopAuthError as e:
        raise HTTPException(401, str(e))


# ── Analytics endpoints ──────────────────────────


@app.get("/api/analytics/fitness-fatigue")
def get_fitness_fatigue(db: Session = Depends(get_db)):
    return calculate_fitness_fatigue(db, date.today())


@app.get("/api/analytics/acwr")
def get_acwr(db: Session = Depends(get_db)):
    return calculate_acwr(db, date.today())


@app.get("/api/analytics/weekly-summary")
def get_weekly_summary(week_start: Optional[date] = None, db: Session = Depends(get_db)):
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    return weekly_summary(db, week_start)


@app.get("/api/analytics/2k-prediction")
def get_2k_prediction(db: Session = Depends(get_db)):
    prediction = predict_2k_from_benchmarks(db)
    if not prediction:
        raise HTTPException(404, "Not enough benchmark data for prediction")
    return prediction


# ── Training plan endpoints ──────────────────────────


@app.post("/api/plan/generate")
def generate_plan(db: Session = Depends(get_db)):
    result = generate_full_plan(db)
    return result


@app.get("/api/plan/workouts")
def get_planned_workouts(
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if not start:
        start = date.today()
    if not end:
        end = start + timedelta(days=13)

    workouts = db.query(PlannedWorkout).filter(
        PlannedWorkout.date >= start,
        PlannedWorkout.date <= end,
    ).order_by(PlannedWorkout.date).all()

    return [
        {
            "id": w.id,
            "date": w.date.isoformat(),
            "workout_type": w.workout_type,
            "title": w.title,
            "description": w.description,
            "target_split": format_split(w.target_split_seconds) if w.target_split_seconds else None,
            "target_spm": f"{w.target_spm_low}-{w.target_spm_high}" if w.target_spm_low else None,
            "target_hr": f"{w.target_hr_low}-{w.target_hr_high}" if w.target_hr_low else None,
            "status": w.status,
            "was_adjusted": w.was_adjusted,
            "adjustment_reason": w.adjustment_reason,
        }
        for w in workouts
    ]


@app.get("/api/plan/phases")
def get_phases(db: Session = Depends(get_db)):
    phases = db.query(TrainingPhase).order_by(TrainingPhase.start_date).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "focus": p.focus,
            "target_weekly_volume_m": p.target_weekly_volume_m,
            "target_intensity_split": p.target_intensity_split,
        }
        for p in phases
    ]


# ── AI coaching endpoints ──────────────────────────


@app.get("/api/coach/weekly-analysis")
def get_weekly_analysis(week_start: Optional[date] = None, db: Session = Depends(get_db)):
    if not week_start:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    coach = CoachAgent()
    analysis = coach.weekly_analysis(db, week_start)
    return {"week_start": week_start.isoformat(), "analysis": analysis}


@app.post("/api/coach/chat")
def coach_chat(request: ChatRequest, db: Session = Depends(get_db)):
    coach = CoachAgent()
    response = coach.chat(db, request.question)
    return {"question": request.question, "response": response}


@app.get("/api/coach/check-adjustments")
def check_adjustments(db: Session = Depends(get_db)):
    coach = CoachAgent()
    response = coach.check_plan_adjustments(db, date.today())
    return {"date": date.today().isoformat(), "analysis": response}
