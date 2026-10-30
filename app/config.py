"""Application configuration, driven by environment variables with local-first defaults."""

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Backend Data API")
    version: str = os.getenv("APP_VERSION", "1.0.0")
    # SQLite by default so the service runs anywhere with zero setup.
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
    # Bundled sample dataset used by the ETL job; override to point at real data.
    data_file: Path = Path(os.getenv("DATA_FILE", BASE_DIR / "data" / "sample_events.csv"))
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")


settings = Settings()
