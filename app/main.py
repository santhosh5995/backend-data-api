"""FastAPI application entrypoint."""

from fastapi import FastAPI

from .config import settings
from .database import Base, engine
from .routers import metrics, pipelines, runs
from .schemas import HealthOut

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.version)

app.include_router(pipelines.router, prefix=settings.api_prefix)
app.include_router(runs.router, prefix=settings.api_prefix)
app.include_router(metrics.router, prefix=settings.api_prefix)


@app.get("/health", response_model=HealthOut, tags=["meta"])
def health():
    return HealthOut(status="ok", app=settings.app_name, version=settings.version)


@app.get("/", tags=["meta"])
def root():
    return {"service": settings.app_name, "version": settings.version, "docs": "/docs"}
