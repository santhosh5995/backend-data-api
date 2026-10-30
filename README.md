# Backend Data API

A production-style Python backend service built with **FastAPI** that manages
data-pipeline definitions and their job runs. Triggering a run executes a real
ETL step in a background task — it reads a CSV dataset, computes aggregates,
persists the results — and a metrics endpoint serves rollups across all
completed runs.

Built as a portfolio project demonstrating API design, background task
processing, layered architecture (routers → services → models), typed
schemas, automated tests, and containerization.

## Features

- **Pipelines API** — create, list, fetch, and delete named data pipelines.
- **Job runs** — trigger a run for a pipeline; the run executes an ETL step
  (CSV ingest → per-category aggregation) in a background task and records
  its lifecycle: `queued → running → success | failed`, with row counts,
  timestamps, error messages, and a JSON result summary.
- **Metrics API** — totals across all runs: rows processed, total amount,
  run success/failure counts, and per-category breakdowns.
- **Config via environment variables** with local-first defaults (SQLite, no
  external services required).
- **Test suite** — end-to-end tests with FastAPI's `TestClient`, including a
  ground-truth check of the ETL aggregates against the sample CSV.

## Architecture

```
backend-data-api/
├── app/
│   ├── main.py            # FastAPI app wiring, /health, router registration
│   ├── config.py          # Settings from environment variables
│   ├── database.py        # SQLAlchemy engine / session factory
│   ├── models.py          # Pipeline and JobRun ORM models
│   ├── schemas.py         # Pydantic request/response models
│   ├── routers/
│   │   ├── pipelines.py   # Pipeline CRUD endpoints
│   │   ├── runs.py        # Run trigger / list / detail endpoints
│   │   └── metrics.py     # Aggregated metrics endpoint
│   └── services/
│       └── etl.py         # ETL step executed by background tasks
├── data/
│   └── sample_events.csv  # Bundled sample dataset (24 events)
├── tests/
│   ├── conftest.py        # Throwaway SQLite DB + ground-truth fixtures
│   └── test_api.py        # End-to-end API tests
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

A run's ETL step uses its own database session (background tasks outlive the
request), and failures are recorded on the run row (`status=failed` plus an
error message) instead of being swallowed.

## API endpoints

Base prefix: `/api/v1` (configurable via `API_PREFIX`). Interactive docs at
`/docs`.

| Method | Path                              | Description                          |
| ------ | --------------------------------- | ------------------------------------ |
| GET    | `/health`                         | Service health check                 |
| POST   | `/api/v1/pipelines`               | Create a pipeline                    |
| GET    | `/api/v1/pipelines`               | List pipelines                       |
| GET    | `/api/v1/pipelines/{id}`          | Get one pipeline                     |
| DELETE | `/api/v1/pipelines/{id}`          | Delete a pipeline (and its runs)     |
| POST   | `/api/v1/pipelines/{id}/runs`     | Trigger a run (202, runs async ETL)  |
| GET    | `/api/v1/runs`                    | List runs (`?pipeline_id=`, `?status=`) |
| GET    | `/api/v1/runs/{id}`               | Get one run with its summary         |
| GET    | `/api/v1/metrics`                 | Aggregates across all completed runs |

### Example session

```bash
# Create a pipeline
curl -s -X POST localhost:8000/api/v1/pipelines \
  -H 'Content-Type: application/json' \
  -d '{"name": "daily-events-etl", "description": "Loads sample events"}'

# Trigger a run (executes the ETL step in the background)
curl -s -X POST localhost:8000/api/v1/pipelines/1/runs

# Check the run — status, rows processed, aggregate summary
curl -s localhost:8000/api/v1/runs/1

# Rollup metrics across all runs
curl -s localhost:8000/api/v1/metrics
```

Example metrics response:

```json
{
  "total_pipelines": 1,
  "total_runs": 1,
  "successful_runs": 1,
  "failed_runs": 0,
  "total_rows_processed": 24,
  "total_amount": 817.19,
  "by_category": {
    "click":    {"count": 9, "total_amount": 0.0},
    "signup":   {"count": 4, "total_amount": 0.0},
    "purchase": {"count": 9, "total_amount": 887.17},
    "refund":   {"count": 2, "total_amount": -69.98}
  }
}
```

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000  (docs at /docs, health at /health)
```

## Run with Docker

```bash
docker compose up --build
# → http://localhost:8000
```

The SQLite database is persisted in a named volume (`api-data`).

## Run the tests

```bash
pytest -v
```

Tests run against a throwaway SQLite database and verify: health check,
pipeline creation (plus duplicate-name and validation errors), a triggered
run completing the ETL with correct row counts, and the metrics endpoint
matching ground-truth aggregates computed from the sample CSV.

## Configuration

| Variable       | Default                          | Purpose                        |
| -------------- | -------------------------------- | ------------------------------ |
| `APP_NAME`     | `Backend Data API`               | Service name                   |
| `APP_VERSION`  | `1.0.0`                          | Service version                |
| `DATABASE_URL` | `sqlite:///<project>/app.db`     | SQLAlchemy database URL        |
| `DATA_FILE`    | `<project>/data/sample_events.csv` | CSV the ETL step processes   |
| `API_PREFIX`   | `/api/v1`                        | Prefix for the versioned API   |

## Tech stack

Python · FastAPI · Uvicorn · SQLAlchemy · Pydantic · SQLite · pytest · Docker
