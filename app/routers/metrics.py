"""Metrics endpoint: aggregates rolled up from all completed runs."""

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import JobRun, Pipeline
from ..schemas import MetricsOut

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    runs = db.query(JobRun).all()
    successful = [r for r in runs if r.status == JobRun.STATUS_SUCCESS]
    failed = [r for r in runs if r.status == JobRun.STATUS_FAILED]

    by_category = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
    total_amount = 0.0
    for run in successful:
        for category, totals in (run.summary or {}).get("by_category", {}).items():
            by_category[category]["count"] += totals["count"]
            by_category[category]["total_amount"] = round(
                by_category[category]["total_amount"] + totals["total_amount"], 2
            )
        total_amount += (run.summary or {}).get("total_amount", 0.0)

    return MetricsOut(
        total_pipelines=db.query(Pipeline).count(),
        total_runs=len(runs),
        successful_runs=len(successful),
        failed_runs=len(failed),
        total_rows_processed=sum(r.rows_processed for r in successful),
        total_amount=round(total_amount, 2),
        by_category=dict(by_category),
    )
