"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AegisScan API"


def test_readiness_check(client):
    """Test readiness endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AegisScan" in data["message"]


def test_list_assessments_empty(client):
    """Test listing assessments when empty."""
    response = client.get("/api/assessments")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_create_assessment_without_authorization(client):
    """Test that assessment creation requires authorization."""
    assessment_data = {
        "name": "Test Assessment",
        "target_url": "http://localhost:3000",
        "authorization_confirmed": False
    }
    response = client.post("/api/assessments", json=assessment_data)
    assert response.status_code == 400
    assert "authorization" in response.json()["detail"].lower()


def test_create_assessment_without_target(client):
    """Test that assessment requires target."""
    assessment_data = {
        "name": "Test Assessment",
        "authorization_confirmed": True
    }
    response = client.post("/api/assessments", json=assessment_data)
    assert response.status_code == 400
    assert "target" in response.json()["detail"].lower()


def test_create_and_get_assessment(client):
    """Test creating and retrieving an assessment."""
    assessment_data = {
        "name": "Test Assessment",
        "target_url": "http://localhost:3000",
        "authorization_confirmed": True
    }

    # Create
    create_response = client.post("/api/assessments", json=assessment_data)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == assessment_data["name"]
    assert created["target_url"] == assessment_data["target_url"]

    # Get
    get_response = client.get(f"/api/assessments/{created['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == created["id"]


def test_list_findings(client):
    """Test listing findings."""
    response = client.get("/api/findings")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
