"""
Unit and integration tests for Phase 2: Target Management, Assessment Wizard & Scan Configuration.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_create_target_success(client):
    """Test creating a valid web target."""
    payload = {
        "name": "World Monitor Test Target",
        "description": "Local test target for unit testing",
        "target_type": "web",
        "base_url": "http://localhost:5173",
        "environment": "local",
        "authorization_status": "authorized",
        "notes": "Verified local test environment"
    }
    response = client.post("/api/targets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["target_type"] == "web"
    assert data["base_url"] == payload["base_url"]
    assert data["authorization_status"] == "authorized"
    assert "id" in data


def test_create_target_invalid_url(client):
    """Test creating target with invalid/unsupported URL scheme."""
    payload = {
        "name": "Invalid Scheme Target",
        "target_type": "web",
        "base_url": "ftp://malicious-server.local/exploit",
        "environment": "local",
        "authorization_status": "authorized"
    }
    response = client.post("/api/targets", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_create_target_no_location(client):
    """Test creating target without any location (base_url, source_path, repository_path)."""
    payload = {
        "name": "Missing Location Target",
        "target_type": "web",
        "environment": "local",
        "authorization_status": "authorized"
    }
    response = client.post("/api/targets", json=payload)
    assert response.status_code == 400
    assert "location" in response.json()["detail"].lower()


def test_list_and_get_targets(client):
    """Test listing targets with filtering and retrieving single target."""
    # Create target
    payload = {
        "name": "Target List Test",
        "target_type": "source_code",
        "source_path": "./src/app",
        "environment": "local",
        "authorization_status": "authorized"
    }
    create_res = client.post("/api/targets", json=payload)
    assert create_res.status_code == 201
    target_id = create_res.json()["id"]

    # List targets
    list_res = client.get("/api/targets?target_type=source_code")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(t["id"] == target_id for t in list_data["items"])

    # Get single target
    get_res = client.get(f"/api/targets/{target_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == payload["name"]


def test_update_and_delete_target(client):
    """Test updating and deleting a target."""
    # Create
    create_res = client.post("/api/targets", json={
        "name": "To Be Updated",
        "target_type": "web",
        "base_url": "http://localhost:8080",
        "environment": "staging",
        "authorization_status": "pending"
    })
    target_id = create_res.json()["id"]

    # Update
    update_res = client.put(f"/api/targets/{target_id}", json={
        "name": "Updated Target Name",
        "authorization_status": "authorized"
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Target Name"
    assert update_res.json()["authorization_status"] == "authorized"

    # Delete
    del_res = client.delete(f"/api/targets/{target_id}")
    assert del_res.status_code == 204

    # Verify 404 on get
    assert client.get(f"/api/targets/{target_id}").status_code == 404


def test_world_monitor_preset_endpoint(client):
    """Test fetching World Monitor predefined preset."""
    response = client.get("/api/assessments/presets/world-monitor")
    assert response.status_code == 200
    data = response.json()
    assert "World Monitor" in data["name"]
    assert data["environment"] == "local"
    assert data["authorization_confirmed"] is True
    assert "modules" in data
    assert "scan_settings" in data


def test_assessment_validation_endpoint(client):
    """Test validation endpoint with valid and invalid configurations."""
    # Invalid: no authorization
    invalid_payload = {
        "name": "Unauthorized Assessment",
        "target_url": "http://localhost:3000",
        "authorization_confirmed": False
    }
    val_res = client.post("/api/assessments/validate", json=invalid_payload)
    assert val_res.status_code == 200
    result = val_res.json()
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0

    # Valid configuration
    valid_payload = {
        "name": "Safe Local Assessment",
        "target_url": "http://localhost:3000",
        "authorization_confirmed": True,
        "scan_settings": {
            "rate_limit": "low",
            "crawl_depth": 2,
            "timeout": 60,
            "active_testing": False
        }
    }
    val_res = client.post("/api/assessments/validate", json=valid_payload)
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True


def test_create_assessment_with_target_link(client):
    """Test creating an assessment linked to a registered target."""
    # 1. Create target
    target_res = client.post("/api/targets", json={
        "name": "Parent Target",
        "target_type": "web",
        "base_url": "http://localhost:5000",
        "environment": "local",
        "authorization_status": "authorized"
    })
    target_id = target_res.json()["id"]

    # 2. Create assessment referencing target
    assessment_payload = {
        "name": "Linked Assessment",
        "target_id": target_id,
        "authorization_confirmed": True,
        "modules": {
            "dast": True,
            "nuclei": True,
            "sast": False,
            "sca": True,
            "custom_checks": True
        },
        "scan_settings": {
            "rate_limit": "low",
            "crawl_depth": 2,
            "timeout": 30,
            "follow_redirects": True,
            "passive_checks": True,
            "active_testing": False
        }
    }
    create_res = client.post("/api/assessments", json=assessment_payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["target_id"] == target_id
    assert created["target_url"] == "http://localhost:5000"
    assert created["target_name"] == "Parent Target"
    assert created["enable_semgrep"] is False  # Synchronized with modules.sast=False
    assert created["enable_zap"] is True
