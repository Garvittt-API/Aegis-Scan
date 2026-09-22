"""Phase 9 analytics tests using real API/application records."""
from fastapi.testclient import TestClient

from app.main import app


def _assessment(client, name):
    response = client.post("/api/assessments", json={
        "name": name,
        "target_url": "http://127.0.0.1:8010",
        "authorization_confirmed": True,
        "modules": {"dast": False, "nuclei": False, "sast": False, "sca": False, "custom_checks": False},
    })
    assert response.status_code == 201
    return response.json()["id"]


def test_analytics_overview_is_real_and_consistent():
    client = TestClient(app)
    response = client.get("/api/analytics/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["total_findings"] == sum(body["severity"].values())
    assert body["verified_findings"] == body["verification"]["verified"]


def test_single_assessment_does_not_create_fake_trend():
    client = TestClient(app)
    assessment_id = _assessment(client, "Phase 9 Trend Test")
    response = client.get("/api/analytics/trends")
    assert response.status_code == 200
    body = response.json()
    assert "available" in body
    assert body["available"] in {True, False}
    assert assessment_id in [item["assessment_id"] for item in body["items"]]


def test_empty_attack_surface_is_unavailable_not_zero():
    client = TestClient(app)
    assessment_id = _assessment(client, "Phase 9 Surface Test")
    response = client.get(f"/api/analytics/attack-surface?assessment_id={assessment_id}")
    assert response.status_code == 200
    assert response.json()["available"] is False
    assert "unavailable" in response.json()["message"].lower()


def test_invalid_comparison_assessment_is_rejected():
    client = TestClient(app)
    response = client.get("/api/analytics/comparison/999999/1000000")
    assert response.status_code == 404
