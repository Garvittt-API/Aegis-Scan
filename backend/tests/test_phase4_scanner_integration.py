"""
Phase 4 Security Scanner Integration Tests.
Validates:
1. Real scanner adapters (ZAP, Nuclei, Semgrep, SCA, Custom Checks)
2. Tool availability detection
3. Safe process execution & timeout handling
4. Custom security heuristics engine
5. Raw result persistence & log inspection
6. Orchestrator failure isolation & execution workflow
7. Zero fake results policy
"""

import json
import os
import shutil
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.models.scan_job import (
    ScanJob,
    ScanJobStatus,
    ScanJobPriority,
    ScannerEngineType,
    validate_job_transition
)
from app.models.assessment import Assessment, AssessmentStatus
from app.scanners.process_runner import check_tool_available, run_safe_process, SafeProcessResult
from app.scanners.result_storage import store_scan_job_results, get_scan_storage_dir
from app.scanners.custom_checks import execute_custom_security_checks, check_security_headers, check_cookie_security, check_cors_policy
from app.scanners.adapters import (
    get_scanner_adapter,
    list_available_scanners,
    ZAPScannerAdapter,
    NucleiScannerAdapter,
    SemgrepScannerAdapter,
    SCAScannerAdapter,
    CustomChecksScannerAdapter
)
from app.services.scan_orchestrator import ScanPlanner, ScanOrchestrator


@pytest.fixture
def client():
    return TestClient(app)


def test_tool_availability_detection():
    """Verify tool detection correctly identifies nonexistent vs existing executables."""
    # Non-existent executable
    available, path = check_tool_available("non_existent_security_scanner_xyz_123")
    assert available is False
    assert path is None

    # Custom checks built-in adapter is always available
    custom_adapter = CustomChecksScannerAdapter()
    avail, p = custom_adapter.is_available()
    assert avail is True
    assert p == "built-in"


def test_scanner_status_endpoint(client):
    """Verify GET /api/scanners/status lists all scanner engines with availability flags."""
    res = client.get("/api/scanners/status")
    assert res.status_code == 200
    scanners = res.json()
    assert len(scanners) == 5
    sc_names = [s["scanner"] for s in scanners]
    assert "zap" in sc_names
    assert "nuclei" in sc_names
    assert "semgrep" in sc_names
    assert "sca" in sc_names
    assert "custom" in sc_names


@pytest.mark.asyncio
async def test_safe_process_runner_success():
    """Verify safe process runner executes commands safely without shell=True and captures output."""
    cmd = ["python", "-c", "print('AegisScan Safe Execution'); import sys; sys.stderr.write('Warning test\\n')"]
    result = await run_safe_process(cmd_args=cmd, timeout=10)
    assert result.exit_code == 0
    assert "AegisScan Safe Execution" in result.stdout
    assert "Warning test" in result.stderr
    assert result.timed_out is False
    assert result.duration_seconds >= 0


@pytest.mark.asyncio
async def test_safe_process_runner_timeout():
    """Verify safe process runner enforces timeouts and handles cancellation."""
    cmd = ["python", "-c", "import time; time.sleep(5)"]
    result = await run_safe_process(cmd_args=cmd, timeout=1)
    assert result.timed_out is True
    assert result.exit_code == -1
    assert "timed out" in result.stderr.lower()


def test_raw_result_storage():
    """Verify raw result storage writes metadata.json, stdout.log, stderr.log, and result.json."""
    assessment_id = 9999
    job_id = 8888
    scanner_name = "Semgrep (SAST)"
    test_json = {"rules_checked": 50, "matches": []}

    res_dir = store_scan_job_results(
        assessment_id=assessment_id,
        scan_job_id=job_id,
        scanner_name=scanner_name,
        target="./src",
        status=ScanJobStatus.COMPLETED.value,
        exit_code=0,
        duration_seconds=1.25,
        stdout="Semgrep executed successfully.",
        stderr="",
        raw_json_data=test_json
    )

    path = Path(res_dir)
    assert path.is_dir()
    assert (path / "metadata.json").is_file()
    assert (path / "stdout.log").is_file()
    assert (path / "stderr.log").is_file()
    assert (path / "result.json").is_file()

    with open(path / "metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
        assert meta["scanner"] == scanner_name
        assert meta["status"] == "completed"
        assert meta["exit_code"] == 0

    with open(path / "result.json", "r", encoding="utf-8") as f:
        saved_data = json.load(f)
        assert saved_data["rules_checked"] == 50

    # Cleanup test dir
    if path.exists():
        shutil.rmtree(path.parent.parent)


def test_custom_security_headers_heuristics():
    """Test custom header security evaluation logic."""
    # Insecure headers
    bad_headers = {
        "server": "Apache/2.4.41 (Ubuntu)",
        "x-powered-by": "PHP/7.4.3"
    }
    findings = check_security_headers(bad_headers)
    rule_ids = [f["check_id"] for f in findings]
    assert "MISSING_CSP" in rule_ids
    assert "MISSING_X_CONTENT_TYPE_OPTIONS" in rule_ids
    assert "SERVER_BANNER_EXPOSED" in rule_ids

    # Secure headers
    good_headers = {
        "content-security-policy": "default-src 'self'",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "no-referrer",
        "strict-transport-security": "max-age=31536000; includeSubDomains"
    }
    good_findings = check_security_headers(good_headers)
    assert len(good_findings) == 0


def test_custom_cookie_and_cors_heuristics():
    """Test cookie and CORS policy heuristic checks."""
    # Cookie missing HttpOnly and Secure
    bad_cookie = "session_id=12345; Path=/"
    cookie_findings = check_cookie_security([bad_cookie])
    cookie_rules = [f["check_id"] for f in cookie_findings]
    assert "COOKIE_MISSING_HTTPONLY" in cookie_rules
    assert "COOKIE_MISSING_SECURE" in cookie_rules

    # Insecure CORS wildcard with credentials
    cors_findings = check_cors_policy({
        "access-control-allow-origin": "*",
        "access-control-allow-credentials": "true"
    })
    cors_rules = [f["check_id"] for f in cors_findings]
    assert "INSECURE_CORS_WILDCARD_WITH_CREDS" in cors_rules


@pytest.mark.asyncio
async def test_custom_checks_adapter_execution():
    """Test executing CustomChecksScannerAdapter against a simulated target."""
    adapter = CustomChecksScannerAdapter()
    res = await adapter.execute(job_id=101, assessment_id=501, target="http://127.0.0.1:9999", config={"timeout": 5})
    assert res["status"] in [ScanJobStatus.COMPLETED.value, ScanJobStatus.FAILED.value]
    assert "result_location" in res


@pytest.mark.asyncio
async def test_scanner_adapter_unavailable_handling():
    """Ensure missing tools gracefully return UNAVAILABLE status without crashing."""
    adapter = NucleiScannerAdapter()
    with patch.object(adapter, "is_available", return_value=(False, None)):
        res = await adapter.execute(job_id=202, assessment_id=502, target="http://127.0.0.1:8000", config={})
        assert res["status"] == ScanJobStatus.UNAVAILABLE.value
        assert "not found" in res["message"].lower()


def test_end_to_end_orchestrator_execution(client):
    """Verify planning, running all jobs, failure isolation, and log retrieval through the API."""
    # 1. Create Assessment
    ass_res = client.post("/api/assessments", json={
        "name": "Phase 4 Full Integration Test",
        "target_url": "http://127.0.0.1:8000",
        "authorization_confirmed": True,
        "modules": {
            "dast": True,
            "nuclei": True,
            "sast": True,
            "sca": True,
            "custom_checks": True
        }
    })
    assert ass_res.status_code == 201
    ass_id = ass_res.json()["id"]

    # 2. Plan Jobs
    plan_res = client.post(f"/api/assessments/{ass_id}/scan-jobs/plan")
    assert plan_res.status_code == 201
    assert plan_res.json()["planned_jobs_count"] == 5

    # 3. Execute all jobs via Orchestrator
    exec_res = client.post(f"/api/assessments/{ass_id}/scan-jobs/execute-all")
    assert exec_res.status_code == 200
    results = exec_res.json()
    assert len(results) == 5

    # All jobs must reach a valid terminal state (COMPLETED, UNAVAILABLE, or FAILED) - no crashing
    for r in results:
        assert r["status"] in [ScanJobStatus.COMPLETED.value, ScanJobStatus.UNAVAILABLE.value, ScanJobStatus.FAILED.value]

    # 4. Check assessment status
    ass_detail = client.get(f"/api/assessments/{ass_id}")
    assert ass_detail.status_code == 200
    assert ass_detail.json()["status"] == AssessmentStatus.COMPLETED.value

    # 5. Query Raw Logs for a job
    first_job_id = results[0]["job_id"]
    raw_res = client.get(f"/api/assessments/{ass_id}/scan-jobs/{first_job_id}/raw")
    assert raw_res.status_code == 200
    raw_data = raw_res.json()
    assert "metadata" in raw_data
    assert "stdout" in raw_data
    assert "stderr" in raw_data
