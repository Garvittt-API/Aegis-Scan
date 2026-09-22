"""Phase 8 report API integration checks."""
from fastapi.testclient import TestClient

from app.main import app


def test_generate_and_fetch_zero_finding_html_report():
    client = TestClient(app)
    assessment = client.post("/api/assessments", json={
        "name": "Phase 8 Report Test",
        "target_url": "http://127.0.0.1:8010",
        "authorization_confirmed": True,
        "modules": {"dast": False, "nuclei": False, "sast": False, "sca": False, "custom_checks": False},
    })
    assert assessment.status_code == 201
    assessment_id = assessment.json()["id"]

    report = client.post("/api/reports", json={"assessment_id": assessment_id, "format": "html"})
    assert report.status_code == 201
    body = report.json()
    assert body["status"] == "completed"
    assert body["content_hash"]

    content = client.get(f"/api/reports/{body['id']}/html")
    assert content.status_code == 200
    assert "No security findings were produced by the executed assessment." in content.text

    latest = client.get(f"/api/reports/assessments/{assessment_id}/report")
    assert latest.status_code == 200
    assert latest.json()["id"] == body["id"]
