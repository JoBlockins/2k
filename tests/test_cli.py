"""Tests for the CLI workout logger — split parser and workout creation."""

import pytest

from scripts.log_workout import parse_split


class TestParseSplit:
    """Test the M:SS.s split parser."""

    def test_basic_split(self):
        assert parse_split("2:15") == 135.0

    def test_split_with_decimal(self):
        assert parse_split("1:45.3") == 105.3

    def test_split_zero_seconds(self):
        assert parse_split("2:00") == 120.0

    def test_split_with_leading_space(self):
        assert parse_split("  2:15  ") == 135.0

    def test_split_single_digit_seconds(self):
        assert parse_split("1:5") == 65.0

    def test_split_sub_two_minutes(self):
        assert parse_split("1:37.5") == 97.5

    def test_invalid_format_no_colon(self):
        with pytest.raises(ValueError, match="Invalid split format"):
            parse_split("135")

    def test_invalid_format_extra_colon(self):
        with pytest.raises(ValueError, match="Invalid split format"):
            parse_split("1:2:3")

    def test_invalid_seconds_over_60(self):
        with pytest.raises(ValueError, match="Seconds must be < 60"):
            parse_split("1:65")

    def test_invalid_empty_string(self):
        with pytest.raises(ValueError, match="Invalid split format"):
            parse_split("")


class TestWorkoutCreation:
    """Test that CLI-created workouts compute derived fields correctly."""

    def test_watts_from_split(self):
        from src.data.metrics import split_to_watts
        # 2:00 split = 120 seconds per 500m → P = 2.80 / (120/500)^3
        watts = split_to_watts(120.0)
        assert round(watts, 1) == 202.5

    def test_trimp_calculation(self):
        from src.data.metrics import calculate_trimp
        trimp = calculate_trimp(duration_minutes=45, avg_hr=148)
        assert trimp > 0
        assert isinstance(trimp, float)

    def test_workout_saved_to_db(self, db):
        from src.models.workout import Workout
        from src.data.metrics import split_to_watts
        from datetime import date

        split_secs = parse_split("2:15")
        workout = Workout(
            date=date(2026, 3, 1),
            workout_type="steady_state",
            source="cli",
            total_distance_m=10000,
            total_time_seconds=2700,
            avg_split_seconds=split_secs,
            avg_watts=round(split_to_watts(split_secs), 1),
        )
        db.add(workout)
        db.commit()

        saved = db.query(Workout).filter(Workout.source == "cli").first()
        assert saved is not None
        assert saved.avg_split_seconds == 135.0
        assert saved.total_distance_m == 10000
