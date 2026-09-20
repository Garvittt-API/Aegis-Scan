"""
Tests for Phase 3: Attack Surface Discovery, URL Normalization, Deduplication, and Scan Orchestrator Foundation.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.discovery.normalizer import normalize_url, generate_asset_fingerprint
from app.models.attack_surface import AttackSurfaceType, AttackSurfaceStatus
from app.models.scan_job import ScanJob, ScanJobStatus, ScanJobPriority, ScannerEngineType, validate_job_transition
from app.scanners.adapters import get_scanner_adapter


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_url_normalization():
    """Test URL normalization rules (ports, redundant slashes, parameter sorting)."""
    # 1. Trailing slash and port removal
    u1 = normalize_url("HTTP://Example.COM:80/path/to/page/")
    assert u1 == "http://example.com/path/to/page"

    # 2. Redundant slash reduction
    u2 = normalize_url("https://api.test.local//v1///users")
    assert u2 == "https://api.test.local/v1/users"

    # 3. Query parameter alphabetical sort
    u3 = normalize_url("http://localhost:5173/search?b=2&a=1&z=99")
    assert u3 == "http://localhost:5173/search?a=1&b=2&z=99"

    # 4. Strip fragments
    u4 = normalize_url("http://localhost:3000/app#dashboard-section")
    assert u4 == "http://localhost:3000/app"


def test_fingerprint_generation():
    """Test deterministic fingerprint generation for identical assets with different ordering."""
    fp1 = generate_asset_fingerprint(
        asset_type=AttackSurfaceType.API,
        url="http://localhost:5173/api/v1/users?limit=10&page=1",
        method="GET"
    )
    fp2 = generate_asset_fingerprint(
        asset_type=AttackSurfaceType.API,
        url="HTTP://LOCALHOST:5173/api/v1/users?page=1&limit=10",
        method="get"
    )
    assert fp1 == fp2


def test_job_state_machine_transitions():
    """Test state machine validity: allowed transitions vs disallowed transitions."""
    # Valid transitions
    assert validate_job_transition(ScanJobStatus.PENDING, ScanJobStatus.QUEUED) is True
    assert validate_job_transition(ScanJobStatus.QUEUED, ScanJobStatus.RUNNING) is True
    assert validate_job_transition(ScanJobStatus.RUNNING, ScanJobStatus.COMPLETED) is True
    assert validate_job_transition(ScanJobStatus.QUEUED, ScanJobStatus.CANCELLED) is True

    # Invalid transitions (must be rejected)
    assert validate_job_transition(ScanJobStatus.COMPLETED, ScanJobStatus.RUNNING) is False
    assert validate_job_transition(ScanJobStatus.FAILED, ScanJobStatus.QUEUED) is False
    assert validate_job_transition(ScanJobStatus.CANCELLED, ScanJobStatus.RUNNING) is False


def test_scanner_adapters_interface():
    """Ensure scanner adapters implement required methods and metadata."""
    for engine in [ScannerEngineType.ZAP, ScannerEngineType.NUCLEI, ScannerEngineType.SEMGREP, ScannerEngineType.SCA, ScannerEngineType.CUSTOM]:
        adapter = get_scanner_adapter(engine)
        assert adapter.engine_type() == engine
        assert adapter.name() is not None
        assert isinstance(adapter.is_available(), tuple)


def test_attack_surface_creation_and_inventory(client):
    """Test creating and retrieving attack surface items and summary stats."""
    # 1. Create Assessment
    ass_res = client.post("/api/assessments", json={
        "name": "Attack Surface Test Assessment",
        "target_url": "http://localhost:5173",
        "authorization_confirmed": True
    })
    assert ass_res.status_code == 201
    ass_id = ass_res.json()["id"]

    # 2. Add an attack surface item manually
    item_res = client.post(f"/api/assessments/{ass_id}/attack-surface", json={
        "type": "api",
        "name": "Users API Endpoint",
        "url": "http://localhost:5173/api/users",
        "method": "GET",
        "source": "crawler"
    })
    assert item_res.status_code == 201
    assert item_res.json()["type"] == "api"

    # 3. Add same item from another source (openapi) to test deduplication
    dup_res = client.post(f"/api/assessments/{ass_id}/attack-surface", json={
        "type": "api",
        "name": "Users API Endpoint",
        "url": "http://localhost:5173/api/users",
        "method": "GET",
        "source": "openapi"
    })
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert "crawler" in dup_data["discovered_by"]
    assert "openapi" in dup_data["discovered_by"]

    # 4. Query attack surface inventory
    list_res = client.get(f"/api/assessments/{ass_id}/attack-surface")
    assert list_res.status_code == 200
    inv = list_res.json()
    assert inv["total"] == 1  # Deduplicated to 1 item
    assert inv["summary"]["apis_count"] == 1


def test_discovery_run_lifecycle(client):
    """Test starting and retrieving discovery run."""
    # Create Assessment
    ass_res = client.post("/api/assessments", json={
        "name": "Discovery Run Test",
        "target_url": "http://localhost:5173",
        "authorization_confirmed": True
    })
    ass_id = ass_res.json()["id"]

    # Launch Discovery Run
    disc_res = client.post(f"/api/assessments/{ass_id}/discovery", json={
        "crawl_depth": 2,
        "max_pages": 10
    })
    assert disc_res.status_code == 202
    run_data = disc_res.json()
    run_id = run_data["id"]
    assert run_data["status"] == "pending"

    # Get Discovery Run Detail
    get_run = client.get(f"/api/assessments/{ass_id}/discovery/{run_id}")
    assert get_run.status_code == 200
    assert get_run.json()["id"] == run_id


def test_scan_plan_generation(client):
    """Test generating scan jobs via ScanPlanner based on assessment configuration."""
    # Create Assessment with specific modules
    ass_res = client.post("/api/assessments", json={
        "name": "Scan Planner Test",
        "target_url": "http://localhost:5173",
        "source_path": "./src",
        "authorization_confirmed": True,
        "modules": {
            "dast": True,
            "nuclei": True,
            "sast": True,
            "sca": False,
            "custom_checks": True
        }
    })
    ass_id = ass_res.json()["id"]

    # Generate Scan Plan
    plan_res = client.post(f"/api/assessments/{ass_id}/scan-jobs/plan", json={
        "priority": "normal"
    })
    assert plan_res.status_code == 201
    plan_data = plan_res.json()
    assert plan_data["planned_jobs_count"] == 4  # ZAP, Nuclei, Semgrep, Custom Checks (SCA is disabled)

    # List scan jobs
    jobs_res = client.get(f"/api/assessments/{ass_id}/scan-jobs")
    assert jobs_res.status_code == 200
    jobs = jobs_res.json()["items"]
    assert len(jobs) == 4
    for j in jobs:
        assert j["status"] == "queued"

    # Test executing job returns a real status
    exec_res = client.post(f"/api/assessments/{ass_id}/scan-jobs/{jobs[0]['id']}/execute")
    assert exec_res.status_code == 200
    assert exec_res.json()["status"] in ["unavailable", "completed", "failed"]
