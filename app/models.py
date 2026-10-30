"""Database models: pipelines and their job runs."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False, index=True)
    source = Column(String(120), nullable=False, default="sample_events.csv")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    runs = relationship("JobRun", back_populates="pipeline", cascade="all, delete-orphan")


class JobRun(Base):
    __tablename__ = "job_runs"

    # Run lifecycle: queued -> running -> success | failed
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=STATUS_QUEUED, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    rows_processed = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    # Aggregates computed by the ETL step, e.g.
    # {"total_amount": 123.4, "by_category": {"purchase": {"count": 3, "total_amount": 99.0}}}
    summary = Column(JSON, nullable=True)

    pipeline = relationship("Pipeline", back_populates="runs")
