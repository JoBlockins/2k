"""Shared test fixtures."""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.database import Base


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_workouts(db):
    """Insert sample workout data for testing."""
    from src.models.workout import Workout

    workouts = []
    base_date = date(2026, 3, 2)  # A Monday

    for i in range(7):
        w = Workout(
            date=base_date + timedelta(days=i),
            workout_type="steady_state" if i < 5 else "rest",
            description=f"Day {i+1} workout",
            source="manual",
            total_distance_m=12000 if i < 5 else None,
            total_time_seconds=3600 if i < 5 else None,
            avg_split_seconds=105.0 if i < 5 else None,  # 1:45
            avg_watts=190 if i < 5 else None,
            avg_spm=20 if i < 5 else None,
            avg_hr=150 if i < 5 else None,
            rpe=5 if i < 5 else None,
            trimp=80.0 if i < 5 else None,
            time_in_zone_1_seconds=1800 if i < 5 else None,
            time_in_zone_2_seconds=1800 if i < 5 else None,
        )
        db.add(w)
        workouts.append(w)

    db.commit()
    return workouts


@pytest.fixture
def sample_benchmarks(db):
    """Insert sample benchmark test data."""
    from src.models.benchmark import BenchmarkTest

    benchmarks = [
        BenchmarkTest(
            date=date(2026, 2, 15),
            test_type="2k",
            total_time_seconds=410.0,  # 6:50
            avg_split_seconds=102.5,   # 1:42.5
            avg_watts=205,
            avg_hr=185,
            max_hr=192,
        ),
        BenchmarkTest(
            date=date(2026, 2, 20),
            test_type="6k",
            total_time_seconds=1296.0,  # 21:36
            avg_split_seconds=108.0,    # 1:48
            avg_watts=175,
            avg_hr=172,
            max_hr=180,
        ),
        BenchmarkTest(
            date=date(2026, 2, 25),
            test_type="30min",
            total_distance_m=7800,
            avg_split_seconds=115.4,
            avg_watts=155,
            avg_hr=168,
        ),
    ]

    for b in benchmarks:
        db.add(b)
    db.commit()
    return benchmarks


@pytest.fixture
def sample_weights(db):
    """Insert sample weight data."""
    from src.models.body import BodyWeight

    weights = []
    base_date = date(2026, 3, 1)

    for i in range(14):
        w = BodyWeight(
            date=base_date + timedelta(days=i),
            weight_lbs=159.5 + (i % 3) * 0.5,  # fluctuates 159.5-160.5
            source="manual",
        )
        db.add(w)
        weights.append(w)

    db.commit()
    return weights
