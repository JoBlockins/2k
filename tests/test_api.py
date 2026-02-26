"""Tests for the FastAPI endpoints."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.database import Base, get_db

# Import all models so Base.metadata knows about all tables
import src.models.workout  # noqa: F401
import src.models.wellness  # noqa: F401
import src.models.benchmark  # noqa: F401
import src.models.body  # noqa: F401
import src.models.strength  # noqa: F401
import src.models.nutrition  # noqa: F401
import src.models.training_plan  # noqa: F401


@pytest.fixture
def client():
    """Create a test client with an in-memory database.

    Uses StaticPool to ensure all sessions share the same connection,
    which is required for SQLite in-memory databases.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    from src.dashboard.api import app

    app.dependency_overrides[get_db] = override_get_db

    # Disable startup event to avoid creating production DB
    original_startup = app.router.on_startup.copy()
    app.router.on_startup.clear()

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()
    app.router.on_startup = original_startup


class TestWorkoutEndpoints:
    def test_create_workout(self, client):
        response = client.post("/api/workouts", json={
            "date": "2026-03-01",
            "workout_type": "steady_state",
            "description": "60min SS",
            "total_distance_m": 14000,
            "total_time_seconds": 3600,
            "avg_split_seconds": 107.1,
            "avg_hr": 148,
            "rpe": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_list_workouts(self, client):
        # Create a workout first
        client.post("/api/workouts", json={
            "date": "2026-03-01",
            "workout_type": "steady_state",
        })

        response = client.get("/api/workouts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_workout_trimp_calculated(self, client):
        response = client.post("/api/workouts", json={
            "date": "2026-03-01",
            "workout_type": "steady_state",
            "total_time_seconds": 3600,
            "avg_hr": 150,
        })
        data = response.json()
        assert data["trimp"] is not None
        assert data["trimp"] > 0


class TestWellnessEndpoints:
    def test_create_wellness(self, client):
        response = client.post("/api/wellness", json={
            "date": "2026-03-01",
            "fatigue": 4,
            "muscle_soreness": 3,
            "stress": 5,
            "mood": 7,
            "sleep_quality_subjective": 8,
        })
        assert response.status_code == 200

    def test_upsert_wellness(self, client):
        # Create
        client.post("/api/wellness", json={
            "date": "2026-03-01",
            "fatigue": 4,
        })
        # Update same date
        response = client.post("/api/wellness", json={
            "date": "2026-03-01",
            "fatigue": 6,
        })
        data = response.json()
        assert data["updated"] is True

    def test_list_wellness(self, client):
        client.post("/api/wellness", json={
            "date": "2026-03-01",
            "fatigue": 4,
        })

        response = client.get("/api/wellness")
        assert response.status_code == 200


class TestWeightEndpoints:
    def test_create_weight(self, client):
        response = client.post("/api/weight", json={
            "date": "2026-03-01",
            "weight_lbs": 159.8,
        })
        assert response.status_code == 200

    def test_weight_trend_no_data(self, client):
        response = client.get("/api/weight/trend")
        assert response.status_code == 404


class TestBenchmarkEndpoints:
    def test_create_benchmark(self, client):
        response = client.post("/api/benchmarks", json={
            "date": "2026-03-01",
            "test_type": "2k",
            "total_time_seconds": 410.0,
            "avg_split_seconds": 102.5,
        })
        assert response.status_code == 200

    def test_list_benchmarks(self, client):
        client.post("/api/benchmarks", json={
            "date": "2026-03-01",
            "test_type": "2k",
            "total_time_seconds": 410.0,
        })

        response = client.get("/api/benchmarks")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_filter_by_type(self, client):
        client.post("/api/benchmarks", json={"date": "2026-03-01", "test_type": "2k", "total_time_seconds": 410.0})
        client.post("/api/benchmarks", json={"date": "2026-03-01", "test_type": "6k", "total_time_seconds": 1296.0})

        response = client.get("/api/benchmarks?test_type=2k")
        assert len(response.json()) == 1


class TestAnalyticsEndpoints:
    def test_fitness_fatigue(self, client):
        response = client.get("/api/analytics/fitness-fatigue")
        assert response.status_code == 200
        data = response.json()
        assert "ctl" in data

    def test_acwr(self, client):
        response = client.get("/api/analytics/acwr")
        assert response.status_code == 200

    def test_weekly_summary(self, client):
        response = client.get("/api/analytics/weekly-summary")
        assert response.status_code == 200

    def test_2k_prediction_no_data(self, client):
        response = client.get("/api/analytics/2k-prediction")
        assert response.status_code == 404


class TestPlanEndpoints:
    def test_generate_plan(self, client):
        response = client.post("/api/plan/generate")
        assert response.status_code == 200
        data = response.json()
        assert data["phases"] == 4
        assert data["total_workouts"] > 0

    def test_get_planned_workouts(self, client):
        # Generate plan first
        client.post("/api/plan/generate")

        response = client.get("/api/plan/workouts")
        assert response.status_code == 200

    def test_get_phases(self, client):
        client.post("/api/plan/generate")

        response = client.get("/api/plan/phases")
        assert response.status_code == 200
        assert len(response.json()) == 4
