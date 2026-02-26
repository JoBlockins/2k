"""AI coaching agent powered by Claude API."""

from datetime import date, timedelta

import anthropic
from sqlalchemy.orm import Session

from cost_tracker import track

from src.agent.prompts import (
    SYSTEM_PROMPT,
    coaching_chat_prompt,
    plan_adjustment_prompt,
    weekly_analysis_prompt,
)
from src.data.config import Config
from src.data.metrics import (
    calculate_acwr,
    calculate_fitness_fatigue,
    predict_2k_from_benchmarks,
    weekly_summary,
    weight_trend,
)
from src.models.training_plan import PlannedWorkout, TrainingPhase
from src.models.wellness import DailyWellness, RecoveryMetrics
from src.models.workout import Workout


class CoachAgent:
    """Claude-powered rowing coach that analyzes data and adjusts training plans."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(api_key=api_key or Config.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5-20250929"

    def weekly_analysis(self, db: Session, week_start: date) -> str:
        """Generate a comprehensive weekly training analysis."""
        data = self._gather_weekly_data(db, week_start)
        prompt = weekly_analysis_prompt(data)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        track("2K", response)
        return response.content[0].text

    def check_plan_adjustments(self, db: Session, as_of: date) -> str:
        """Check if the training plan needs adjustment based on current signals."""
        signals = self._gather_adjustment_signals(db, as_of)
        planned = self._get_upcoming_workouts(db, as_of)

        data = {
            "signals": signals,
            "planned_workouts": [self._workout_to_dict(w) for w in planned],
            "context": {
                "fitness_fatigue": calculate_fitness_fatigue(db, as_of),
                "acwr": calculate_acwr(db, as_of),
                "prediction": predict_2k_from_benchmarks(db),
            },
        }

        prompt = plan_adjustment_prompt(data)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        track("2K", response)
        return response.content[0].text

    def chat(self, db: Session, question: str, as_of: date | None = None) -> str:
        """Answer athlete questions with data-backed coaching responses."""
        as_of = as_of or date.today()
        context = self._gather_chat_context(db, as_of)
        prompt = coaching_chat_prompt(question, context)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        track("2K", response)
        return response.content[0].text

    def _gather_weekly_data(self, db: Session, week_start: date) -> dict:
        """Gather all data needed for weekly analysis."""
        week_end = week_start + timedelta(days=6)

        # Workouts
        workouts = db.query(Workout).filter(
            Workout.date >= week_start, Workout.date <= week_end
        ).order_by(Workout.date).all()

        # Wellness
        wellness = db.query(DailyWellness).filter(
            DailyWellness.date >= week_start, DailyWellness.date <= week_end
        ).order_by(DailyWellness.date).all()

        # Recovery
        recovery = db.query(RecoveryMetrics).filter(
            RecoveryMetrics.date >= week_start, RecoveryMetrics.date <= week_end
        ).order_by(RecoveryMetrics.date).all()

        # Current phase
        phase = db.query(TrainingPhase).filter(
            TrainingPhase.start_date <= week_start, TrainingPhase.end_date >= week_start
        ).first()

        # Calculated metrics
        goal_date = date.fromisoformat(Config.GOAL_DATE)
        weeks_remaining = (goal_date - week_end).days // 7

        return {
            "weekly_summary": weekly_summary(db, week_start),
            "workouts": [self._workout_to_dict(w) for w in workouts],
            "wellness": [self._wellness_to_dict(w) for w in wellness],
            "recovery": self._summarize_recovery(recovery),
            "weight": weight_trend(db, week_end),
            "fitness_fatigue": calculate_fitness_fatigue(db, week_end),
            "acwr": calculate_acwr(db, week_end),
            "prediction": predict_2k_from_benchmarks(db),
            "phase": phase.name if phase else "Unknown",
            "weeks_remaining": weeks_remaining,
        }

    def _gather_adjustment_signals(self, db: Session, as_of: date) -> dict:
        """Gather signals that might trigger plan adjustments."""
        # Recent wellness (last 3 days)
        recent_wellness = db.query(DailyWellness).filter(
            DailyWellness.date >= as_of - timedelta(days=2),
            DailyWellness.date <= as_of,
        ).all()

        # Recent recovery
        latest_recovery = db.query(RecoveryMetrics).filter(
            RecoveryMetrics.date == as_of
        ).first()

        # Build signals
        signals = {
            "date": as_of.isoformat(),
            "fitness_fatigue": calculate_fitness_fatigue(db, as_of),
            "acwr": calculate_acwr(db, as_of),
            "weight": weight_trend(db, as_of),
        }

        if recent_wellness:
            avg_fatigue = sum(w.fatigue or 0 for w in recent_wellness) / len(recent_wellness)
            avg_soreness = sum(w.muscle_soreness or 0 for w in recent_wellness) / len(recent_wellness)
            signals["avg_fatigue_3d"] = round(avg_fatigue, 1)
            signals["avg_soreness_3d"] = round(avg_soreness, 1)

        if latest_recovery:
            signals["hrv"] = latest_recovery.hrv_rmssd
            signals["resting_hr"] = latest_recovery.resting_hr
            signals["whoop_recovery"] = latest_recovery.whoop_recovery_score
            signals["sleep_hours"] = round(latest_recovery.sleep_duration_minutes / 60, 1) if latest_recovery.sleep_duration_minutes else None

        return signals

    def _gather_chat_context(self, db: Session, as_of: date) -> dict:
        """Gather context for answering athlete questions."""
        recent_workouts = db.query(Workout).filter(
            Workout.date >= as_of - timedelta(days=7)
        ).order_by(Workout.date.desc()).limit(5).all()

        phase = db.query(TrainingPhase).filter(
            TrainingPhase.start_date <= as_of, TrainingPhase.end_date >= as_of
        ).first()

        return {
            "prediction": predict_2k_from_benchmarks(db),
            "phase": phase.name if phase else "Unknown",
            "fitness_fatigue": calculate_fitness_fatigue(db, as_of),
            "weight": weight_trend(db, as_of),
            "recent_workouts": [self._workout_to_dict(w) for w in recent_workouts],
            "recovery": None,
        }

    def _get_upcoming_workouts(self, db: Session, as_of: date) -> list:
        """Get planned workouts for the next 7 days."""
        return db.query(PlannedWorkout).filter(
            PlannedWorkout.date >= as_of,
            PlannedWorkout.date <= as_of + timedelta(days=6),
            PlannedWorkout.status == "scheduled",
        ).order_by(PlannedWorkout.date).all()

    @staticmethod
    def _workout_to_dict(w) -> dict:
        """Convert a workout model to a dictionary."""
        if isinstance(w, PlannedWorkout):
            return {
                "date": w.date.isoformat(),
                "title": w.title,
                "workout_type": w.workout_type,
                "description": w.description,
                "target_split_seconds": w.target_split_seconds,
                "target_distance_m": w.target_distance_m,
            }
        return {
            "date": w.date.isoformat(),
            "workout_type": w.workout_type,
            "description": w.description,
            "total_distance_m": w.total_distance_m,
            "total_time_seconds": w.total_time_seconds,
            "avg_split_seconds": w.avg_split_seconds,
            "avg_watts": w.avg_watts,
            "avg_spm": w.avg_spm,
            "avg_hr": w.avg_hr,
            "rpe": w.rpe,
            "trimp": w.trimp,
        }

    @staticmethod
    def _wellness_to_dict(w: DailyWellness) -> dict:
        return {
            "date": w.date.isoformat(),
            "fatigue": w.fatigue,
            "muscle_soreness": w.muscle_soreness,
            "stress": w.stress,
            "mood": w.mood,
            "sleep_quality_subjective": w.sleep_quality_subjective,
        }

    @staticmethod
    def _summarize_recovery(records: list) -> dict:
        if not records:
            return {"status": "no data"}
        latest = records[-1]
        return {
            "latest_hrv": latest.hrv_rmssd,
            "latest_resting_hr": latest.resting_hr,
            "latest_sleep_hours": round(latest.sleep_duration_minutes / 60, 1) if latest.sleep_duration_minutes else None,
            "whoop_recovery": latest.whoop_recovery_score,
            "days_with_data": len(records),
        }
