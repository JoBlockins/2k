# 2K Erg Training AI Agent

AI-powered training coach for rowing ergometer performance, targeting a sub-6:30 2k erg time by August 2026.

## Overview

This system replaces a human coach's feedback loop by ingesting training data from multiple sources, detecting trends, and adjusting the training plan in real time using Claude as the reasoning engine.

**Athlete:** Joshua Dockins, men's lightweight (160 lbs)
**Current 2k:** 6:50 | **Goal:** sub-6:30 | **Timeline:** August 2026

## Architecture

- **Data Pipeline** — Ingests from Concept2 ErgData, Whoop, Withings scale, MyFitnessPal, and manual input
- **AI Agent** — Claude API for weekly analysis, plan adjustments, and 2k predictions
- **Training Plan Engine** — Periodized plan generation with auto-adjustment
- **Web Dashboard** — Streamlit MVP for daily logging, trend visualization, and chat

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -m src.data.init_db

# Run the dashboard
streamlit run src/dashboard/app.py

# Or run the API server
uvicorn src.dashboard.api:app --reload
```

## Project Structure

```
2k/
├── docs/                  # Project documentation
├── src/
│   ├── agent/             # Claude-powered reasoning engine
│   ├── data/              # Data ingestion, storage, pipelines
│   ├── dashboard/         # Web UI (FastAPI + Streamlit)
│   └── models/            # Data models, schemas, predictions
├── data/
│   ├── raw/               # Raw exports from devices/APIs
│   └── processed/         # Cleaned, structured data
├── tests/
├── requirements.txt
└── README.md
```

## Documentation

- [Project Overview](docs/PROJECT_OVERVIEW.md)
- [Metrics & Data](docs/METRICS_AND_DATA.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Training Philosophy](docs/TRAINING_PHILOSOPHY.md)
