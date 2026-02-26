# System Architecture

This document describes the technical architecture of the 2K Erg Training AI Agent, from data ingestion through AI reasoning to the athlete-facing dashboard.

---

## High-Level System Design

The system follows a five-stage pipeline:

```
[Data Ingestion] --> [Storage] --> [Processing] --> [AI Reasoning] --> [Dashboard]
      |                  |              |                 |                |
  APIs, CSV,         SQLite         Derived          Claude API       Streamlit
  Manual Input       (MVP)          Metrics,         structured        + Plotly
                                    Aggregations     prompts
```

### Stage 1: Data Ingestion

External data sources are pulled into the system via scheduled jobs and manual entry points.

### Stage 2: Storage

All raw and processed data lives in a SQLite database (MVP). Schema is managed via SQLAlchemy ORM.

### Stage 3: Processing

Raw data is transformed into derived metrics (TRIMP, ACWR, zone distribution, rolling averages, etc.).

### Stage 4: AI Reasoning

The Claude API analyzes processed data and generates training recommendations, plan adjustments, and performance predictions.

### Stage 5: Dashboard

A Streamlit frontend presents data visualizations and AI-generated insights to the athlete.

---

## Data Pipeline

### External Data Sources

Each data source has a dedicated ingestion module that handles authentication, data fetching, normalization, and storage.

```
src/
  ingestion/
    concept2.py       # Concept2 Logbook API client
    whoop.py          # Whoop API client
    withings.py       # Withings Health Mate API client
    myfitnesspal.py   # MyFitnessPal CSV parser / API client
    manual.py         # Manual input handler (RPE, wellness, strength)
    apple_health.py   # Apple Health XML export parser (fallback)
```

#### Concept2 Logbook API

- **Data:** Erg session results (splits, watts, stroke rate, distance, drag factor, per-stroke data).
- **Auth:** OAuth2 or API key (per Concept2 developer docs).
- **Frequency:** After each session (triggered manually or on a short polling interval).
- **Normalization:** Raw API response is parsed into the `ErgSession` and `ErgInterval` models.

#### Whoop API

- **Data:** Daily recovery (HRV RMSSD, resting HR, sleep duration, sleep quality, recovery score), strain.
- **Auth:** OAuth2 (Whoop developer API).
- **Frequency:** Daily morning pull (recovery data updates after wake-up detection).
- **Normalization:** Mapped to `DailyRecovery` model fields.

#### Withings Health Mate API

- **Data:** Body weight, body composition.
- **Auth:** OAuth2 (Withings developer API).
- **Frequency:** Daily (triggered by scale measurement, typically morning).
- **Normalization:** Weight stored in lbs and kg in the `DailyWeight` model.

#### MyFitnessPal

- **Data:** Daily nutrition (calories, protein, carbs, fat).
- **Auth:** CSV export (primary) or third-party API wrapper (secondary).
- **Frequency:** Daily (end of day or next morning).
- **Normalization:** CSV rows parsed into `DailyNutrition` model.

#### Manual Input

- **Data:** Session RPE (1-10), daily wellness scores (fatigue, soreness, stress, mood, sleep quality), strength test results.
- **Input Method:** Web form on the Streamlit dashboard or API endpoint.
- **Frequency:** RPE after each session; wellness daily; strength monthly.
- **Normalization:** Direct entry into `SessionRPE`, `DailyWellness`, and `StrengthTest` models.

### Data Flow Diagram

```
                    +------------------+
                    |   Concept2 API   |---+
                    +------------------+   |
                    +------------------+   |     +-----------+     +------------+
                    |    Whoop API     |---+---->| Ingestion |---->|   SQLite   |
                    +------------------+   |     |  Layer    |     |  Database  |
                    +------------------+   |     +-----------+     +-----+------+
                    |  Withings API    |---+                             |
                    +------------------+   |                             v
                    +------------------+   |                    +----------------+
                    | MyFitnessPal CSV |---+                    |  Processing    |
                    +------------------+   |                    |  Layer         |
                    +------------------+   |                    +-------+--------+
                    |  Manual Input    |---+                            |
                    +------------------+                                v
                                                              +-----------------+
                                                              |  AI Reasoning   |
                                                              |  (Claude API)   |
                                                              +-------+---------+
                                                                      |
                                                                      v
                                                              +-----------------+
                                                              |   Dashboard     |
                                                              |  (Streamlit)    |
                                                              +-----------------+
```

---

## Storage: SQLite (MVP)

SQLite is the MVP database choice for simplicity, zero-configuration deployment, and sufficient performance for a single-athlete application. If the system scales to multiple athletes or requires concurrent access, migration to PostgreSQL is straightforward via SQLAlchemy.

### Database Schema Overview

The schema is defined via SQLAlchemy ORM models in `src/models/`. Key tables:

#### Core Training Data

```
erg_sessions
  - id (PK)
  - date (DATE)
  - workout_type (VARCHAR)        # e.g., "steady_state", "interval", "2k_test"
  - total_distance (INT)          # meters
  - total_time (FLOAT)            # seconds
  - avg_split (FLOAT)             # seconds per 500m
  - avg_watts (FLOAT)
  - avg_spm (FLOAT)               # strokes per minute
  - avg_drive_length (FLOAT)      # meters
  - drag_factor (INT)
  - avg_hr (INT)                  # average heart rate
  - max_hr (INT)
  - notes (TEXT)
  - created_at (TIMESTAMP)

erg_intervals
  - id (PK)
  - session_id (FK -> erg_sessions)
  - interval_number (INT)
  - distance (INT)
  - time (FLOAT)
  - split (FLOAT)
  - watts (FLOAT)
  - spm (FLOAT)
  - avg_hr (INT)
  - rest_time (FLOAT)             # seconds of rest before this interval

session_rpe
  - id (PK)
  - session_id (FK -> erg_sessions)
  - rpe (INT)                     # 1-10
  - notes (TEXT)
  - created_at (TIMESTAMP)
```

#### Recovery & Physiological Data

```
daily_recovery
  - id (PK)
  - date (DATE, UNIQUE)
  - resting_hr (INT)              # bpm
  - hrv_rmssd (FLOAT)             # ms
  - sleep_duration (FLOAT)        # hours
  - sleep_quality (FLOAT)         # percentage or score
  - recovery_score (FLOAT)        # Whoop recovery %
  - strain_score (FLOAT)          # Whoop strain
  - source (VARCHAR)              # "whoop", "polar", "manual"
  - created_at (TIMESTAMP)

daily_weight
  - id (PK)
  - date (DATE, UNIQUE)
  - weight_lbs (FLOAT)
  - weight_kg (FLOAT)
  - body_fat_pct (FLOAT)          # nullable
  - source (VARCHAR)              # "withings", "manual"
  - created_at (TIMESTAMP)
```

#### Nutrition

```
daily_nutrition
  - id (PK)
  - date (DATE, UNIQUE)
  - calories (INT)                # kcal
  - protein_g (FLOAT)
  - carbs_g (FLOAT)
  - fat_g (FLOAT)
  - hydration_l (FLOAT)           # liters, nullable
  - source (VARCHAR)              # "myfitnesspal", "manual"
  - created_at (TIMESTAMP)
```

#### Wellness & Strength

```
daily_wellness
  - id (PK)
  - date (DATE, UNIQUE)
  - fatigue (INT)                 # 1-10
  - muscle_soreness (INT)         # 1-10
  - stress (INT)                  # 1-10
  - mood (INT)                    # 1-10
  - sleep_quality (INT)           # 1-10
  - readiness_score (FLOAT)       # calculated composite
  - created_at (TIMESTAMP)

strength_tests
  - id (PK)
  - date (DATE)
  - exercise (VARCHAR)            # "deadlift", "squat", "bench_pull", etc.
  - weight_lbs (FLOAT)
  - reps (INT)
  - estimated_1rm (FLOAT)
  - bw_ratio (FLOAT)              # calculated
  - notes (TEXT)
  - created_at (TIMESTAMP)
```

#### Benchmark Tests

```
benchmark_tests
  - id (PK)
  - date (DATE)
  - test_type (VARCHAR)           # "2k", "6k", "30min", "500m", "step"
  - result_time (FLOAT)           # seconds (for timed tests)
  - result_distance (INT)         # meters (for timed tests like 30min)
  - avg_split (FLOAT)
  - avg_watts (FLOAT)
  - avg_spm (FLOAT)
  - avg_hr (INT)
  - max_hr (INT)
  - predicted_2k (FLOAT)          # seconds, calculated from result
  - notes (TEXT)
  - created_at (TIMESTAMP)
```

#### Training Plan & AI

```
training_plan
  - id (PK)
  - week_number (INT)
  - phase (VARCHAR)               # "base_1", "base_2", "build", "peak"
  - planned_volume_m (INT)        # meters
  - planned_intensity_dist (JSON) # e.g., {"ut2": 80, "ut1": 10, "at": 10}
  - sessions (JSON)               # array of planned sessions
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)

ai_analysis
  - id (PK)
  - date (DATE)
  - analysis_type (VARCHAR)       # "weekly", "benchmark", "adjustment", "prediction"
  - input_summary (JSON)          # metrics fed to Claude
  - output (TEXT)                  # Claude's response
  - recommendations (JSON)        # structured recommendations
  - model_used (VARCHAR)          # Claude model version
  - created_at (TIMESTAMP)
```

---

## Processing Layer

The processing layer sits between raw stored data and the AI reasoning engine. It computes derived metrics and aggregations.

```
src/
  processing/
    training_load.py    # TRIMP, TSS, ACWR calculations
    zone_calculator.py  # HR zone classification and distribution
    predictions.py      # 2k prediction models from benchmark data
    aggregations.py     # Weekly/monthly rollups, rolling averages
    readiness.py        # Daily readiness score from wellness data
    weight_tracker.py   # 7-day rolling average, trend analysis
```

### Key Calculations

**TRIMP (Training Impulse):**
```
TRIMP = duration (min) x avg_HR_fraction x intensity_weighting
where avg_HR_fraction = (session_avg_HR - resting_HR) / (max_HR - resting_HR)
```

**Acute:Chronic Workload Ratio:**
```
ACWR = acute_load (7-day rolling avg) / chronic_load (28-day rolling avg)
Target range: 0.8 - 1.3
```

**Zone Distribution:**
Heart rate zones are defined per athlete threshold and split into:
- UT2 (< 75% max HR), UT1 (75-80%), AT (80-85%), TR (85-90%), AN (> 90%)
- Weekly percentage in each zone is computed and compared to the 80/20 target.

**2k Prediction:**
```
From 6k:  predicted_2k_split = avg_6k_split - 5 to 7 seconds
From 30min: predicted_2k_split derived from avg_split and known correlations
Composite: weighted average of multiple predictors with confidence interval
```

---

## AI Reasoning Engine

The AI reasoning engine uses the Claude API (via the `anthropic` Python SDK) to perform analysis that goes beyond simple calculations. It synthesizes data across all tiers and generates human-readable coaching insights.

```
src/
  ai/
    engine.py           # Core Claude API interaction layer
    prompts/
      weekly_analysis.py    # Weekly training review prompt
      plan_adjustment.py    # Training plan modification prompt
      prediction.py         # 2k performance prediction prompt
      coaching.py           # Contextual coaching explanation prompt
      race_plan.py          # 2k race pacing strategy prompt
```

### AI Analysis Types

#### 1. Weekly Analysis (Every Sunday/Monday)

**Input to Claude:**
- Week's training sessions (volume, intensity, splits, HR data)
- Zone distribution vs. target
- ACWR and training load trend
- Recovery metrics (HRV, RHR, sleep averages)
- Wellness score trend
- Weight trend
- Nutrition summary

**Output from Claude:**
- Summary of the training week
- What went well
- Areas of concern
- Comparison to plan
- Recommendations for the coming week

#### 2. Plan Adjustment (As needed)

**Input to Claude:**
- Current phase and week within phase
- Planned vs. actual training for recent weeks
- Latest benchmark results vs. targets
- Recovery and readiness trends
- Any flags (injury, illness, weight issues, ACWR out of range)

**Output from Claude:**
- Specific adjustments to the coming week's plan
- Rationale for each adjustment
- Updated predictions if benchmarks changed

#### 3. 2k Prediction (After each benchmark test)

**Input to Claude:**
- All benchmark test results to date with dates
- Current training phase and volume
- Historical trend of predictions
- Time remaining until August 2026

**Output from Claude:**
- Current predicted 2k time with confidence range
- On-track assessment (ahead / on target / behind)
- What needs to happen to close any gap

#### 4. Coaching Explanations (On demand)

**Input to Claude:**
- Athlete's question or area of confusion
- Relevant data context
- Training philosophy reference (from TRAINING_PHILOSOPHY.md)

**Output from Claude:**
- Clear explanation in coaching language
- Data-backed reasoning
- Actionable takeaway

### Prompt Engineering Approach

All prompts follow a structured format:

```python
SYSTEM_PROMPT = """
You are an expert rowing coach and exercise physiologist specializing in
lightweight men's rowing. You are coaching Joshua Dockins, a lightweight
rower (160 lbs) targeting a sub-6:30 2k erg score by August 2026.

Your coaching philosophy is grounded in:
- Polarized training (80/20 intensity distribution)
- Periodized progression (Base -> Build -> Peak)
- Data-driven decision making
- Recovery-first mindset

Current phase: {phase}
Current week: {week_number}
Days until target: {days_remaining}

Always provide specific, actionable recommendations backed by the data.
Explain your reasoning so the athlete understands the "why."
"""
```

Data is passed as structured JSON in the user message. Claude's response is parsed for both free-text analysis and structured recommendations (using tool use or JSON output mode where appropriate).

---

## Training Plan Engine

The training plan engine manages the periodized training structure across the six-month timeline.

```
src/
  planning/
    periodization.py    # Phase definitions and transitions
    session_builder.py  # Individual session generation
    weekly_planner.py   # Weekly plan construction
    adjuster.py         # Plan modification based on AI recommendations
```

### Periodization Phases

| Phase | Dates | Focus | Volume Target | Intensity Split |
|---|---|---|---|---|
| **Base 1** | Feb -- Mar 2026 | Aerobic foundation | 70-90k m/week | 80%+ UT2 |
| **Base 2** | Apr -- May 2026 | Aerobic capacity + tempo | 80-100k m/week | 75/25 |
| **Build** | Jun -- Jul 2026 | Threshold & race pace | 60-80k m/week | 70/30 |
| **Peak & Taper** | Late Jul -- Aug 2026 | Race simulation, sharpening | Decreasing | High quality |

### Session Types

- **Steady State (UT2):** 60-90 min at 1:55-2:05 split, 18-22 SPM. The bread and butter.
- **Tempo / UT1:** 20-40 min at 1:48-1:52 split, 22-26 SPM.
- **Threshold (AT):** Intervals at 1:42-1:46 split. E.g., 4x2k, 3x3k with rest.
- **VO2max / Transport (TR):** Short intervals at 1:36-1:40 split. E.g., 8x500m, 5x1000m.
- **Anaerobic (AN):** Sprint work at 1:25-1:32 split. E.g., 10x250m, 4x500m.
- **Race Simulation:** Full 2k or 2k-pace pieces with race-day strategy.

---

## Dashboard: FastAPI Backend + Streamlit Frontend

### Backend (FastAPI)

```
src/
  api/
    main.py             # FastAPI app entry point
    routes/
      sessions.py       # Erg session CRUD
      recovery.py       # Recovery data endpoints
      nutrition.py      # Nutrition data endpoints
      wellness.py       # Wellness input and readout
      plan.py           # Training plan view and adjustments
      analysis.py       # AI analysis trigger and results
      benchmarks.py     # Benchmark test results
    dependencies.py     # Database session, auth
```

The FastAPI backend provides:

- **REST endpoints** for all data CRUD operations.
- **Trigger endpoints** for on-demand AI analysis.
- **Aggregation endpoints** for dashboard data (weekly summaries, trends).
- **Input endpoints** for manual data entry (RPE, wellness, strength).

### Frontend (Streamlit MVP)

```
src/
  dashboard/
    app.py              # Main Streamlit app
    pages/
      overview.py       # Daily snapshot: readiness, weight, plan for today
      training_log.py   # Session history with charts
      benchmarks.py     # Benchmark test results and 2k predictions
      recovery.py       # HRV, RHR, sleep trends
      nutrition.py      # Macro tracking and weight trend
      plan.py           # Weekly/monthly training plan view
      analysis.py       # AI coaching insights and recommendations
      input.py          # Manual data entry forms
```

The Streamlit dashboard provides:

- **Daily Overview:** Today's plan, readiness score, weight, AI notes.
- **Training Log:** Session history with split/watts/HR charts (Plotly).
- **Benchmark Tracker:** Test results over time with 2k prediction trendline.
- **Recovery Dashboard:** HRV, RHR, and sleep trends with annotations.
- **Nutrition View:** Daily macros vs. targets, weight trend overlay.
- **Training Plan:** Calendar view of planned and completed sessions.
- **AI Insights:** Weekly analysis, plan adjustments, coaching Q&A.
- **Input Forms:** Quick entry for RPE, wellness, strength, manual data.

### Visualization (Plotly)

All charts use Plotly for interactive, zoomable visualizations:

- Time-series line charts for splits, watts, HR, weight, HRV, etc.
- Zone distribution bar charts (stacked).
- Benchmark progress scatter plots with prediction trendlines.
- Training load area charts with ACWR overlay.
- Gauge charts for daily readiness and weight status.

---

## Tech Stack Summary

| Component | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11+ | Core application language |
| **ORM** | SQLAlchemy 2.0 | Database models and queries |
| **Database** | SQLite (MVP) | Data storage |
| **API** | FastAPI | Backend REST API |
| **Frontend** | Streamlit | MVP dashboard |
| **Visualization** | Plotly | Interactive charts |
| **AI** | Claude API (anthropic SDK) | Reasoning engine |
| **Data Ingestion** | httpx / requests | API clients for external services |
| **Task Scheduling** | APScheduler (or cron) | Periodic data pulls |
| **Testing** | pytest | Unit and integration tests |
| **Linting** | ruff | Code quality |
| **Type Checking** | mypy | Static type analysis |

---

## Project Directory Structure

```
2k/
  docs/
    PROJECT_OVERVIEW.md
    METRICS_AND_DATA.md
    ARCHITECTURE.md
    TRAINING_PHILOSOPHY.md
  src/
    __init__.py
    models/
      __init__.py
      base.py                # SQLAlchemy base, engine, session
      erg.py                 # ErgSession, ErgInterval
      recovery.py            # DailyRecovery, DailyWeight
      nutrition.py           # DailyNutrition
      wellness.py            # DailyWellness
      strength.py            # StrengthTest
      benchmark.py           # BenchmarkTest
      plan.py                # TrainingPlan
      analysis.py            # AIAnalysis
    ingestion/
      __init__.py
      concept2.py
      whoop.py
      withings.py
      myfitnesspal.py
      manual.py
      apple_health.py
    processing/
      __init__.py
      training_load.py
      zone_calculator.py
      predictions.py
      aggregations.py
      readiness.py
      weight_tracker.py
    ai/
      __init__.py
      engine.py
      prompts/
        __init__.py
        weekly_analysis.py
        plan_adjustment.py
        prediction.py
        coaching.py
        race_plan.py
    planning/
      __init__.py
      periodization.py
      session_builder.py
      weekly_planner.py
      adjuster.py
    api/
      __init__.py
      main.py
      routes/
        __init__.py
        sessions.py
        recovery.py
        nutrition.py
        wellness.py
        plan.py
        analysis.py
        benchmarks.py
      dependencies.py
    dashboard/
      __init__.py
      app.py
      pages/
        __init__.py
        overview.py
        training_log.py
        benchmarks.py
        recovery.py
        nutrition.py
        plan.py
        analysis.py
        input.py
  data/
    training.db             # SQLite database file
  tests/
    __init__.py
    test_models.py
    test_ingestion.py
    test_processing.py
    test_ai.py
    test_api.py
  requirements.txt
  README.md
```
