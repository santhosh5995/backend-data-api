"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, examples=["daily-events-etl"])
    source: str = Field(default="sample_events.csv", max_length=120)
    description: Optional[str] = None


class PipelineOut(BaseModel):
    id: int
    name: str
    source: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunOut(BaseModel):
    id: int
    pipeline_id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    rows_processed: int
    error_message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryTotals(BaseModel):
    count: int
    total_amount: float


class MetricsOut(BaseModel):
    total_pipelines: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    total_rows_processed: int
    total_amount: float
    by_category: Dict[str, CategoryTotals]


class HealthOut(BaseModel):
    status: str
    app: str
    version: str
