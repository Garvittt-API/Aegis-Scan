"""
Raw scan results storage manager.
Saves stdout, stderr, metadata, and structured raw JSON per scan job.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.core.config import settings


def get_scan_storage_dir(assessment_id: int, scan_job_id: int) -> Path:
    """
    Construct storage directory path for a scan job:
    reports/assessments/{assessment_id}/scans/{scan_job_id}/
    """
    base_dir = settings.reports_dir or Path("./reports")
    scan_dir = base_dir / "assessments" / str(assessment_id) / "scans" / str(scan_job_id)
    scan_dir.mkdir(parents=True, exist_ok=True)
    return scan_dir


def store_scan_job_results(
    assessment_id: int,
    scan_job_id: int,
    scanner_name: str,
    target: str,
    status: str,
    exit_code: int,
    duration_seconds: float,
    stdout: str,
    stderr: str,
    raw_json_data: Optional[Any] = None,
    configuration: Optional[Dict[str, Any]] = None
) -> str:
    """
    Persist raw scanner execution artifacts. Returns directory path string.
    """
    scan_dir = get_scan_storage_dir(assessment_id, scan_job_id)

    # 1. Write metadata.json
    metadata = {
        "assessment_id": assessment_id,
        "scan_job_id": scan_job_id,
        "scanner": scanner_name,
        "target": target,
        "status": status,
        "exit_code": exit_code,
        "duration_seconds": duration_seconds,
        "configuration": configuration or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(scan_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # 2. Write stdout.log & stderr.log
    with open(scan_dir / "stdout.log", "w", encoding="utf-8") as f:
        f.write(stdout or "")

    with open(scan_dir / "stderr.log", "w", encoding="utf-8") as f:
        f.write(stderr or "")

    # 3. Write result.json
    if raw_json_data is not None:
        with open(scan_dir / "result.json", "w", encoding="utf-8") as f:
            if isinstance(raw_json_data, (dict, list)):
                json.dump(raw_json_data, f, indent=2)
            else:
                f.write(str(raw_json_data))
    else:
        # Fallback empty result json
        with open(scan_dir / "result.json", "w", encoding="utf-8") as f:
            json.dump({"raw_output": stdout or "", "scanner": scanner_name}, f, indent=2)

    result_path_str = str(scan_dir)
    logger.info(f"RAW_RESULT_STORED: scan_job_id={scan_job_id} path='{result_path_str}'")
    return result_path_str
