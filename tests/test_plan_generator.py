"""Tests for the training plan generator."""

from datetime import date

from src.agent.plan_generator import (
    WEEKLY_TEMPLATES,
    WORKOUT_TEMPLATES,
    create_training_phases,
    generate_weekly_plan,
)
from src.models.training_plan import PlannedWorkout, TrainingPhase


class TestWorkoutTemplates:
    def test_all_templates_have_required_fields(self):
        for key, template in WORKOUT_TEMPLATES.items():
            assert "title" in template, f"{key} missing title"
            assert "workout_type" in template, f"{key} missing workout_type"
            assert "description" in template, f"{key} missing description"

    def test_all_weekly_templates_reference_valid_workouts(self):
        for phase, template in WEEKLY_TEMPLATES.items():
            for session_key in template["sessions"]:
                assert session_key in WORKOUT_TEMPLATES, f"{phase} references unknown workout: {session_key}"


class TestCreatePhases:
    def test_creates_four_phases(self, db):
        phases = create_training_phases(db)
        assert len(phases) == 4

    def test_phases_are_chronological(self, db):
        phases = create_training_phases(db)
        for i in range(len(phases) - 1):
            assert phases[i].end_date < phases[i + 1].start_date or \
                   phases[i].end_date <= phases[i + 1].start_date

    def test_phases_cover_feb_to_aug(self, db):
        phases = create_training_phases(db)
        assert phases[0].start_date.month == 2
        assert phases[-1].end_date.month == 8

    def test_phase_names(self, db):
        phases = create_training_phases(db)
        names = [p.name for p in phases]
        assert names == ["base_1", "base_2", "build", "peak"]


class TestGenerateWeeklyPlan:
    def test_generates_workouts_for_base_1(self, db):
        phase = TrainingPhase(
            name="base_1",
            start_date=date(2026, 2, 9),
            end_date=date(2026, 3, 29),
            focus="Aerobic foundation",
            target_weekly_volume_m=80000,
        )
        db.add(phase)
        db.commit()
        db.refresh(phase)

        workouts = generate_weekly_plan(db, date(2026, 2, 9), phase)
        assert len(workouts) == 8  # 7 days + 1 extra (Wed has 2)
        assert all(isinstance(w, PlannedWorkout) for w in workouts)

    def test_split_targets_are_reasonable(self, db):
        phase = TrainingPhase(
            name="base_1",
            start_date=date(2026, 2, 9),
            end_date=date(2026, 3, 29),
            focus="Aerobic foundation",
            target_weekly_volume_m=80000,
        )
        db.add(phase)
        db.commit()
        db.refresh(phase)

        workouts = generate_weekly_plan(
            db, date(2026, 2, 9), phase,
            current_2k_split=102.5,  # 1:42.5
        )

        for w in workouts:
            if w.target_split_seconds:
                # Steady state should be slower than 2k pace
                assert w.target_split_seconds > 102.5, \
                    f"{w.title} has split {w.target_split_seconds} which is faster than 2k pace"
