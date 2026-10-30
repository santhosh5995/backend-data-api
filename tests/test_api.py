"""End-to-end API tests using FastAPI's TestClient."""

from .conftest import API


def _create_pipeline(client, name="daily-events-etl"):
    resp = client.post(f"{API}/pipelines", json={"name": name, "description": "Loads sample events"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"]
    assert body["version"]


def test_create_pipeline(client):
    pipeline = _create_pipeline(client, name="create-test")
    assert pipeline["name"] == "create-test"
    assert pipeline["source"] == "sample_events.csv"
    assert pipeline["id"] >= 1
    # And it is fetchable.
    resp = client.get(f"{API}/pipelines/{pipeline['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "create-test"


def test_create_pipeline_duplicate_name_rejected(client):
    _create_pipeline(client, name="dupe-test")
    resp = client.post(f"{API}/pipelines", json={"name": "dupe-test"})
    assert resp.status_code == 400


def test_create_pipeline_validation_error(client):
    # Missing required "name" -> pydantic validation error.
    resp = client.post(f"{API}/pipelines", json={"description": "no name"})
    assert resp.status_code == 422
    # Empty name also fails min_length.
    resp = client.post(f"{API}/pipelines", json={"name": ""})
    assert resp.status_code == 422


def test_trigger_run_completes_etl(client, expected_totals):
    pipeline = _create_pipeline(client, name="run-test")
    resp = client.post(f"{API}/pipelines/{pipeline['id']}/runs")
    assert resp.status_code == 202, resp.text
    run_id = resp.json()["id"]

    # TestClient executes background tasks before returning, so the run is done.
    resp = client.get(f"{API}/runs/{run_id}")
    assert resp.status_code == 200
    run = resp.json()
    assert run["status"] == "success"
    assert run["rows_processed"] == expected_totals["rows"]
    assert run["summary"]["total_amount"] == expected_totals["total_amount"]
    assert run["started_at"] is not None and run["finished_at"] is not None


def test_trigger_run_unknown_pipeline_404(client):
    resp = client.post(f"{API}/pipelines/999999/runs")
    assert resp.status_code == 404


def test_metrics_endpoint_returns_stored_aggregates(client, expected_totals):
    pipeline = _create_pipeline(client, name="metrics-test")
    resp = client.post(f"{API}/pipelines/{pipeline['id']}/runs")
    assert resp.status_code == 202

    resp = client.get(f"{API}/metrics")
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["total_pipelines"] >= 1
    assert metrics["successful_runs"] >= 1
    assert metrics["total_rows_processed"] >= expected_totals["rows"]
    assert metrics["total_amount"] >= expected_totals["total_amount"]
    purchases = metrics["by_category"]["purchase"]
    expected_purchases = expected_totals["by_category"]["purchase"]
    assert purchases["count"] >= expected_purchases["count"]
    assert purchases["total_amount"] >= round(expected_purchases["total_amount"], 2)
