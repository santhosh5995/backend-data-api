"""Test fixtures: run the app against a throwaway SQLite database."""

import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a temp DB *before* importing it.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

API = settings.api_prefix


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def expected_totals():
    """Ground truth computed straight from the bundled CSV."""
    import csv
    from collections import defaultdict

    by_category = defaultdict(lambda: {"count": 0, "total_amount": 0.0})
    rows = 0
    total = 0.0
    with open(Path(settings.data_file), newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            amount = float(row["amount"])
            by_category[row["category"]]["count"] += 1
            by_category[row["category"]]["total_amount"] += amount
            total += amount
            rows += 1
    return {"rows": rows, "total_amount": round(total, 2), "by_category": dict(by_category)}
