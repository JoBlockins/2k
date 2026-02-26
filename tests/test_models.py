"""Tests for data models and database operations."""

from datetime import date

from src.models.benchmark import BenchmarkTest, StepTestResult
from src.models.body import BodyWeight
from src.models.nutrition import DailyNutrition
from src.models.strength import StrengthBenchmark, StrengthExercise, StrengthSession
from src.models.training_plan import PlannedWorkout, TrainingPhase, WeeklyPlan
from src.models.wellness import DailyWellness, RecoveryMetrics
from src.models.workout import Workout, WorkoutInterval


class TestWorkoutModel:
    def test_create_workout(self, db):
        workout = Workout(
            date=date(2026, 3, 1),
            workout_type="steady_state",
            description="60min SS",
            source="manual",
            total_distance_m=14000,
            total_time_seconds=3600,
            avg_split_seconds=107.1,
            avg_watts=180,
            avg_spm=20,
            avg_hr=148,
            rpe=5,
        )
        db.add(workout)
        db.commit()

        result = db.query(Workout).first()
        assert result.workout_type == "steady_state"
        assert result.total_distance_m == 14000
        assert result.avg_hr == 148

    def test_create_workout_intervals(self, db):
        workout = Workout(
            date=date(2026, 3, 1),
            workout_type="interval",
            source="manual",
        )
        db.add(workout)
        db.commit()

        for i in range(4):
            interval = WorkoutInterval(
                workout_id=workout.id,
                interval_number=i + 1,
                distance_m=2000,
                time_seconds=420 + i * 2,
                split_seconds=105 + i * 0.5,
            )
            db.add(interval)
        db.commit()

        intervals = db.query(WorkoutInterval).filter_by(workout_id=workout.id).all()
        assert len(intervals) == 4


class TestWellnessModel:
    def test_create_wellness(self, db):
        wellness = DailyWellness(
            date=date(2026, 3, 1),
            fatigue=4,
            muscle_soreness=3,
            stress=5,
            mood=7,
            sleep_quality_subjective=8,
        )
        db.add(wellness)
        db.commit()

        result = db.query(DailyWellness).first()
        assert result.fatigue == 4
        assert result.mood == 7


class TestRecoveryModel:
    def test_create_recovery(self, db):
        recovery = RecoveryMetrics(
            date=date(2026, 3, 1),
            resting_hr=48,
            hrv_rmssd=65.0,
            sleep_duration_minutes=480,
            deep_sleep_minutes=110,
            rem_sleep_minutes=120,
            whoop_recovery_score=85.0,
        )
        db.add(recovery)
        db.commit()

        result = db.query(RecoveryMetrics).first()
        assert result.hrv_rmssd == 65.0
        assert result.whoop_recovery_score == 85.0


class TestBenchmarkModel:
    def test_create_2k_test(self, db):
        test = BenchmarkTest(
            date=date(2026, 3, 1),
            test_type="2k",
            total_time_seconds=410.0,
            avg_split_seconds=102.5,
            avg_watts=205,
            avg_hr=185,
            max_hr=192,
        )
        db.add(test)
        db.commit()

        result = db.query(BenchmarkTest).first()
        assert result.test_type == "2k"
        assert result.total_time_seconds == 410.0

    def test_step_test(self, db):
        test = BenchmarkTest(
            date=date(2026, 3, 1),
            test_type="step",
        )
        db.add(test)
        db.commit()

        for i in range(5):
            step = StepTestResult(
                benchmark_test_id=test.id,
                step_number=i + 1,
                target_split_seconds=120 - i * 5,
                actual_split_seconds=120.5 - i * 5,
                avg_hr=140 + i * 8,
            )
            db.add(step)
        db.commit()

        steps = db.query(StepTestResult).filter_by(benchmark_test_id=test.id).all()
        assert len(steps) == 5


class TestTrainingPlanModel:
    def test_create_phase(self, db):
        phase = TrainingPhase(
            name="base_1",
            start_date=date(2026, 2, 9),
            end_date=date(2026, 3, 29),
            focus="Aerobic foundation",
            target_weekly_volume_m=80000,
            target_intensity_split="80/20",
        )
        db.add(phase)
        db.commit()

        result = db.query(TrainingPhase).first()
        assert result.name == "base_1"
        assert result.target_weekly_volume_m == 80000

    def test_create_planned_workout(self, db):
        planned = PlannedWorkout(
            date=date(2026, 3, 2),
            workout_type="steady_state",
            title="60min Steady State",
            description="60 minutes at UT2 pace",
            target_time_seconds=3600,
            target_split_seconds=117.5,
            target_spm_low=18,
            target_spm_high=22,
            target_hr_low=137,
            target_hr_high=156,
            status="scheduled",
        )
        db.add(planned)
        db.commit()

        result = db.query(PlannedWorkout).first()
        assert result.title == "60min Steady State"
        assert result.status == "scheduled"


class TestBodyWeightModel:
    def test_create_weight(self, db):
        weight = BodyWeight(
            date=date(2026, 3, 1),
            weight_lbs=159.8,
            source="manual",
        )
        db.add(weight)
        db.commit()

        result = db.query(BodyWeight).first()
        assert result.weight_lbs == 159.8


class TestNutritionModel:
    def test_create_nutrition(self, db):
        nutrition = DailyNutrition(
            date=date(2026, 3, 1),
            calories=2800,
            protein_g=150.0,
            carbs_g=350.0,
            fat_g=80.0,
        )
        db.add(nutrition)
        db.commit()

        result = db.query(DailyNutrition).first()
        assert result.calories == 2800
        assert result.protein_g == 150.0


class TestStrengthModel:
    def test_create_strength_benchmark(self, db):
        sb = StrengthBenchmark(
            date=date(2026, 3, 1),
            exercise_name="deadlift",
            test_type="5rm",
            weight_lbs=315.0,
            bodyweight_lbs=160.0,
            bw_ratio=1.97,
        )
        db.add(sb)
        db.commit()

        result = db.query(StrengthBenchmark).first()
        assert result.exercise_name == "deadlift"
        assert result.bw_ratio == 1.97
