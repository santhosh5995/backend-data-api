"""Job-run endpoints: trigger a run (background ETL), list runs, fetch one run."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import JobRun, Pipeline
from ..schemas import RunOut
from ..services.etl import execute_run

router = APIRouter(tags=["runs"])


@router.post(
    "/pipelines/{pipeline_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_run(pipeline_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    pipeline = db.get(Pipeline, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    run = JobRun(pipeline_id=pipeline.id, status=JobRun.STATUS_QUEUED)
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(execute_run, run.id, settings.data_file)
    return run


@router.get("/runs", response_model=List[RunOut])
def list_runs(
    pipeline_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(JobRun)
    if pipeline_id is not None:
        query = query.filter(JobRun.pipeline_id == pipeline_id)
    if status_filter is not None:
        query = query.filter(JobRun.status == status_filter)
    return query.order_by(JobRun.id.desc()).all()


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(JobRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
