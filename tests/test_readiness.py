import pytest
from fastapi import status

def test_readiness_endpoint_unauthenticated(client):
    """Readiness should be public for orchestration tools."""
    response = client.get("/api/v1/admin/readiness")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert data["status"] in ["READY", "DEGRADED"]
    assert "database" in data
    assert "redis" in data

def test_version_endpoint_unauthenticated(client):
    """Version should be public for easy debugging."""
    response = client.get("/api/v1/admin/version")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["service_name"] == "Outfit AI Backend"
    assert "api_version" in data
    assert "build_time" in data
