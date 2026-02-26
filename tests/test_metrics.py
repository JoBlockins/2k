"""Tests for the derived metrics engine."""

from datetime import date

from src.data.metrics import (
    calculate_acwr,
    calculate_fitness_fatigue,
    calculate_trimp,
    classify_hr_zone,
    format_split,
    format_time,
    get_hr_zones,
    predict_2k_from_6k,
    predict_2k_from_30min,
    predict_2k_from_benchmarks,
    split_to_watts,
    watts_to_split,
    weekly_summary,
    weight_trend,
)


class TestRowingPhysics:
    def test_split_to_watts_known_values(self):
        # 2:00/500m split = 120 seconds. Concept2 formula: P = 2.80 / (pace_per_meter)^3
        # pace_per_meter = 120/500 = 0.24 s/m. Watts = 2.80 / 0.24^3 ≈ 202.5W
        watts = split_to_watts(120.0)
        assert 200 < watts < 210  # ~202.5W at 2:00

    def test_watts_to_split_inverse(self):
        original_split = 105.0  # 1:45
        watts = split_to_watts(original_split)
        recovered_split = watts_to_split(watts)
        assert abs(recovered_split - original_split) < 0.01

    def test_format_split(self):
        assert format_split(97.5) == "1:37.5"
        assert format_split(102.5) == "1:42.5"
        assert format_split(120.0) == "2:00.0"

    def test_format_time(self):
        assert format_time(410.0) == "6:50.0"
        assert format_time(390.0) == "6:30.0"
        assert format_time(3600.0) == "1:00:00.0"

    def test_goal_watts(self):
        # Sub-6:30 = 1:37.5 split = 97.5 seconds per 500m
        watts = split_to_watts(97.5)
        assert watts > 230  # should be ~235W

    def test_current_watts(self):
        # Current 6:50 = 1:42.5 split = 102.5 seconds per 500m
        watts = split_to_watts(102.5)
        assert watts > 200  # should be ~205W


class TestTrainingZones:
    def test_get_hr_zones(self):
        zones = get_hr_zones(195)
        assert zones["UT2"] == (107, 136)
        assert zones["AN"][1] == 195

    def test_classify_hr_zone(self):
        assert classify_hr_zone(130, 195) == "UT2"
        assert classify_hr_zone(150, 195) == "UT1"
        assert classify_hr_zone(160, 195) == "AT"
        assert classify_hr_zone(170, 195) == "TR"
        assert classify_hr_zone(185, 195) == "AN"


class TestTRIMP:
    def test_trimp_basic(self):
        trimp = calculate_trimp(
            duration_minutes=60,
            avg_hr=150,
            resting_hr=50,
            max_hr=195,
        )
        assert trimp > 0
        assert trimp < 200  # reasonable range for 60min SS

    def test_trimp_higher_hr_means_higher_trimp(self):
        trimp_low = calculate_trimp(60, avg_hr=140, resting_hr=50, max_hr=195)
        trimp_high = calculate_trimp(60, avg_hr=170, resting_hr=50, max_hr=195)
        assert trimp_high > trimp_low

    def test_trimp_longer_means_higher(self):
        trimp_short = calculate_trimp(30, avg_hr=150, resting_hr=50, max_hr=195)
        trimp_long = calculate_trimp(60, avg_hr=150, resting_hr=50, max_hr=195)
        assert trimp_long > trimp_short


class TestFitnessFatigue:
    def test_fitness_fatigue_with_data(self, db, sample_workouts):
        result = calculate_fitness_fatigue(db, date(2026, 3, 8))
        assert "ctl" in result
        assert "atl" in result
        assert "tsb" in result
        assert "status" in result
        assert result["atl"] > result["ctl"]  # acute load should be higher with recent training

    def test_fitness_fatigue_no_data(self, db):
        result = calculate_fitness_fatigue(db, date(2026, 3, 8))
        assert result["ctl"] == 0
        assert result["atl"] == 0


class TestACWR:
    def test_acwr_with_data(self, db, sample_workouts):
        result = calculate_acwr(db, date(2026, 3, 8))
        assert "acwr" in result
        assert "risk" in result

    def test_acwr_no_data(self, db):
        result = calculate_acwr(db, date(2026, 3, 8))
        assert result["risk"] == "insufficient_data"


class TestWeeklySummary:
    def test_weekly_summary(self, db, sample_workouts):
        result = weekly_summary(db, date(2026, 3, 2))
        assert result["total_meters"] == 60000  # 5 x 12000
        assert result["session_count"] == 7  # includes rest days
        assert result["total_trimp"] == 400.0  # 5 x 80

    def test_weekly_summary_empty(self, db):
        result = weekly_summary(db, date(2026, 3, 2))
        assert result["total_meters"] == 0


class TestPredictions:
    def test_predict_2k_from_6k(self):
        # 6k at 1:48 (108s) should predict ~1:42 (102s) for 2k
        predicted = predict_2k_from_6k(108.0)
        assert 100 < predicted < 104

    def test_predict_2k_from_30min(self):
        # 7800m in 30min ≈ 1:55 pace, predict ~1:49 2k
        predicted_time = predict_2k_from_30min(7800)
        assert 380 < predicted_time < 440  # reasonable 2k time range

    def test_predict_from_benchmarks(self, db, sample_benchmarks):
        result = predict_2k_from_benchmarks(db)
        assert result is not None
        assert "predicted_2k_time" in result
        assert "gap_seconds" in result
        assert result["predicted_2k_time"] > 0


class TestWeightTrend:
    def test_weight_trend(self, db, sample_weights):
        result = weight_trend(db, date(2026, 3, 14))
        assert result is not None
        assert result["target"] == 160.0
        assert result["status"] in ["on_target", "slightly_over", "slightly_under", "over", "under"]

    def test_weight_trend_no_data(self, db):
        result = weight_trend(db, date(2026, 3, 14))
        assert result is None
