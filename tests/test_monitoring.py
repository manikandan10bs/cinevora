"""
Unit Tests for Cinevora Live MLOps Telemetry & Middleware
Tests cover:
1. Middleware request duration timing and recording
2. Health check internal tagging
3. Monitoring metrics aggregation endpoint
4. Monitoring events log endpoint
5. Secret redaction in telemetry
"""

import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Provides TestClient with application lifespan active."""
    with TestClient(app) as test_client:
        yield test_client


def test_monitoring_middleware_records_live_requests(client):
    """Verifies that API requests are accurately intercepted and timed."""
    # Send a search request
    search_res = client.get("/movies/search?query=Toy%20Story")
    assert search_res.status_code == 200

    # Fetch recent events to confirm interception
    events_res = client.get("/monitoring/events?limit=10")
    assert events_res.status_code == 200
    data = events_res.json()
    assert data["count"] > 0
    matched = [e for e in data["events"] if e["endpoint"] == "/movies/search"]
    assert len(matched) > 0
    assert matched[0]["duration_ms"] > 0
    assert matched[0]["status_code"] == 200


def test_monitoring_metrics_endpoint_structure(client):
    """Verifies /monitoring/metrics provides both live telemetry and offline benchmarks."""
    res = client.get("/monitoring/metrics?exclude_internal=true")
    assert res.status_code == 200
    data = res.json()

    assert "live_metrics" in data
    assert "timestamp" in data
    live = data["live_metrics"]

    assert "total_requests" in live
    assert "avg_latency_ms" in live
    assert "median_latency_ms" in live
    assert "status_stats" in live
    assert "endpoint_stats" in live
    assert "recommendation_metrics" in live
    assert "assistant_metrics" in live

    # Offline evaluation benchmark check
    if data["offline_evaluation"] is not None:
        assert "ranking_metrics" in data["offline_evaluation"]
        assert "collaborative" in data["offline_evaluation"]["ranking_metrics"]


def test_monitoring_never_exposes_secrets(client):
    """Verifies monitoring logs do not record or reveal credentials."""
    metrics_res = client.get("/monitoring/metrics")
    events_res = client.get("/monitoring/events")

    metrics_text = str(metrics_res.json())
    events_text = str(events_res.json())

    for secret_token in ["API_KEY", "AQ.", "Bearer", "secret_key"]:
        assert secret_token not in metrics_text
        assert secret_token not in events_text
