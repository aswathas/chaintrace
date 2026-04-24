"""Integration tests for API health endpoint."""
import pytest


def test_health_endpoint(client):
    """Verify GET /health returns 200 with expected keys."""
    if client is None:
        pytest.skip("FastAPI client not available")

    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "version" in data or "timestamp" in data
