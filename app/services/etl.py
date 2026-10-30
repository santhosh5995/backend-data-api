"""The ETL step executed by a job run.

Reads the bundled sample events CSV, computes per-category aggregates and
overall totals, and persists the result on the JobRun row. Runs in a FastAPI
background task with its own database session.
"""

import csv
from collections import defaultdict
from pathlib import Path

from ..database import SessionLocal
from ..models import JobRun, utcnow


def compute_aggregates(csv_path: Path) -> dict:
    """Aggregate a CSV of events with columns: event_id, timestamp, category, amount."""
    by_category = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
    rows = 0
    total_amount = 0.0
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"category", "amount"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV is missing required columns: {sorted(required)}")
        for row in reader:
            amount = float(row["amount"])
            bucket = by_category[row["category"]]
            bucket["count"] += 1
            bucket["total_amount"] = round(bucket["total_amount"] + amount, 2)
            total_amount += amount
            rows += 1
    return {
        "total_amount": round(total_amount, 2),
        "avg_amount": round(total_amount / rows, 2) if rows else 0.0,
        "by_category": dict(by_category),
    }


def execute_run(run_id: int, data_file: Path) -> None:
    """Execute the ETL step for one run, recording status, row counts, and summary."""
    db = SessionLocal()
    try:
        run = db.get(JobRun, run_id)
        if run is None:
            return
        run.status = JobRun.STATUS_RUNNING
        run.started_at = utcnow()
        db.commit()
        try:
            summary = compute_aggregates(data_file)
            run.summary = summary
            run.rows_processed = sum(c["count"] for c in summary["by_category"].values())
            run.status = JobRun.STATUS_SUCCESS
        except Exception as exc:  # any ETL failure is recorded, never swallowed
            run.status = JobRun.STATUS_FAILED
            run.error_message = f"{type(exc).__name__}: {exc}"
            run.rows_processed = 0
        run.finished_at = utcnow()
        db.commit()
    finally:
        db.close()
