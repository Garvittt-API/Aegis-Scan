"""
Production-grade real scanner adapter implementations for AegisScan.
Integrates OWASP ZAP, Nuclei, Semgrep, Dependency-Check, and Custom Security Checks.
Enforces tool availability detection, process execution, and raw result persistence.
"""

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from app.core.config import settings
from app.models.scan_job import ScannerEngineType, ScanJobStatus
from app.scanners.base import ScannerAdapter
from app.scanners.process_runner import check_tool_available, run_safe_process
from app.scanners.result_storage import store_scan_job_results, get_scan_storage_dir
from app.scanners.custom_checks import execute_custom_security_checks


class ZAPScannerAdapter(ScannerAdapter):
    """OWASP ZAP Dynamic Application Security Testing Adapter."""

    def name(self) -> str:
        return "OWASP ZAP (DAST)"

    def engine_type(self) -> ScannerEngineType:
        return ScannerEngineType.ZAP

    def is_available(self) -> tuple[bool, Optional[str]]:
        return check_tool_available("zap.sh", settings.zap_path) or check_tool_available("zap.bat", settings.zap_path) or check_tool_available("zap", settings.zap_path)

    def validate_config(self, config: Optional[Dict[str, Any]]) -> bool:
        return True

    def prepare(self, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "engine": "zap",
            "target": target,
            "spider_depth": config.get("crawl_depth", 2) if config else 2,
            "timeout": config.get("timeout", 60) if config else 60,
            "active_testing": config.get("active_testing", False) if config else False,
            "prepared_at": datetime.utcnow().isoformat()
        }

    async def execute(self, job_id: int, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        available, exec_path = self.is_available()
        if not available:
            logger.warning(f"ZAP executable not found for job {job_id}")
            result_dir = store_scan_job_results(
                assessment_id=assessment_id,
                scan_job_id=job_id,
                scanner_name=self.name(),
                target=target,
                status=ScanJobStatus.UNAVAILABLE.value,
                exit_code=-1,
                duration_seconds=0,
                stdout="",
                stderr="OWASP ZAP executable was not found on the system PATH or configured ZAP_PATH.",
                raw_json_data={"error": "ZAP not installed or not in PATH", "scanner": "zap"}
            )
            return {
                "status": ScanJobStatus.UNAVAILABLE.value,
                "message": "OWASP ZAP executable was not found on the system PATH or configured ZAP_PATH.",
                "result_location": result_dir
            }

        scan_dir = get_scan_storage_dir(assessment_id, job_id)
        report_file = scan_dir / "zap_report.json"
        timeout = config.get("timeout", 180) if config else 180

        # Execute ZAP automation / quick command line
        cmd = [
            exec_path,
            "-cmd",
            "-quickurl", target,
            "-quickout", str(report_file)
        ]

        proc_result = await run_safe_process(cmd_args=cmd, cwd=str(scan_dir), timeout=timeout)

        raw_data = None
        if report_file.is_file():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception:
                raw_data = {"raw_stdout": proc_result.stdout}

        final_status = ScanJobStatus.COMPLETED.value if proc_result.exit_code == 0 else ScanJobStatus.FAILED.value
        if proc_result.timed_out:
            final_status = ScanJobStatus.TIMEOUT.value

        result_dir = store_scan_job_results(
            assessment_id=assessment_id,
            scan_job_id=job_id,
            scanner_name=self.name(),
            target=target,
            status=final_status,
            exit_code=proc_result.exit_code,
            duration_seconds=proc_result.duration_seconds,
            stdout=proc_result.stdout,
            stderr=proc_result.stderr,
            raw_json_data=raw_data
        )

        return {
            "status": final_status,
            "exit_code": proc_result.exit_code,
            "duration_seconds": proc_result.duration_seconds,
            "result_location": result_dir
        }

    def cancel(self, job_id: int) -> bool:
        return True

    def parse_results(self, result_location: Optional[str]) -> List[Dict[str, Any]]:
        return []


class NucleiScannerAdapter(ScannerAdapter):
    """Nuclei Template-based Vulnerability Scanner Adapter."""

    def name(self) -> str:
        return "Nuclei (Templates)"

    def engine_type(self) -> ScannerEngineType:
        return ScannerEngineType.NUCLEI

    def is_available(self) -> tuple[bool, Optional[str]]:
        return check_tool_available("nuclei", settings.nuclei_path)

    def validate_config(self, config: Optional[Dict[str, Any]]) -> bool:
        return True

    def prepare(self, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "engine": "nuclei",
            "target": target,
            "rate_limit": config.get("rate_limit", "low") if config else "low",
            "timeout": config.get("timeout", 60) if config else 60,
            "prepared_at": datetime.utcnow().isoformat()
        }

    async def execute(self, job_id: int, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        available, exec_path = self.is_available()
        if not available:
            logger.warning(f"Nuclei executable not found for job {job_id}")
            result_dir = store_scan_job_results(
                assessment_id=assessment_id,
                scan_job_id=job_id,
                scanner_name=self.name(),
                target=target,
                status=ScanJobStatus.UNAVAILABLE.value,
                exit_code=-1,
                duration_seconds=0,
                stdout="",
                stderr="Nuclei executable was not found on the system PATH or configured NUCLEI_PATH.",
                raw_json_data={"error": "Nuclei not installed or not in PATH", "scanner": "nuclei"}
            )
            return {
                "status": ScanJobStatus.UNAVAILABLE.value,
                "message": "Nuclei executable was not found on the system PATH or configured NUCLEI_PATH.",
                "result_location": result_dir
            }

        scan_dir = get_scan_storage_dir(assessment_id, job_id)
        report_file = scan_dir / "nuclei_output.json"
        timeout = config.get("timeout", 180) if config else 180
        rate_limit = config.get("rate_limit", "low") if config else "low"
        rate_val = "10" if rate_limit == "low" else ("30" if rate_limit == "medium" else "100")

        cmd = [
            exec_path,
            "-u", target,
            "-json-export", str(report_file),
            "-rate-limit", rate_val,
            "-silent",
            "-stats=false"
        ]

        proc_result = await run_safe_process(cmd_args=cmd, cwd=str(scan_dir), timeout=timeout)

        raw_data = []
        if report_file.is_file():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        raw_data = [json.loads(line) for line in content.splitlines() if line.strip()]
            except Exception:
                raw_data = {"raw_stdout": proc_result.stdout}

        final_status = ScanJobStatus.COMPLETED.value if proc_result.exit_code == 0 else ScanJobStatus.FAILED.value
        if proc_result.timed_out:
            final_status = ScanJobStatus.TIMEOUT.value

        result_dir = store_scan_job_results(
            assessment_id=assessment_id,
            scan_job_id=job_id,
            scanner_name=self.name(),
            target=target,
            status=final_status,
            exit_code=proc_result.exit_code,
            duration_seconds=proc_result.duration_seconds,
            stdout=proc_result.stdout,
            stderr=proc_result.stderr,
            raw_json_data=raw_data
        )

        return {
            "status": final_status,
            "exit_code": proc_result.exit_code,
            "duration_seconds": proc_result.duration_seconds,
            "result_location": result_dir
        }

    def cancel(self, job_id: int) -> bool:
        return True

    def parse_results(self, result_location: Optional[str]) -> List[Dict[str, Any]]:
        return []


class SemgrepScannerAdapter(ScannerAdapter):
    """Semgrep Static Application Security Testing (SAST) Adapter."""

    def name(self) -> str:
        return "Semgrep (SAST)"

    def engine_type(self) -> ScannerEngineType:
        return ScannerEngineType.SEMGREP

    def is_available(self) -> tuple[bool, Optional[str]]:
        return check_tool_available("semgrep", settings.semgrep_path)

    def validate_config(self, config: Optional[Dict[str, Any]]) -> bool:
        return True

    def prepare(self, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "engine": "semgrep",
            "target_path": target,
            "rules": "auto",
            "timeout": config.get("timeout", 120) if config else 120,
            "prepared_at": datetime.utcnow().isoformat()
        }

    async def execute(self, job_id: int, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        available, exec_path = self.is_available()
        if not available:
            logger.warning(f"Semgrep executable not found for job {job_id}")
            result_dir = store_scan_job_results(
                assessment_id=assessment_id,
                scan_job_id=job_id,
                scanner_name=self.name(),
                target=target,
                status=ScanJobStatus.UNAVAILABLE.value,
                exit_code=-1,
                duration_seconds=0,
                stdout="",
                stderr="Semgrep executable was not found on the system PATH or configured SEMGREP_PATH.",
                raw_json_data={"error": "Semgrep not installed or not in PATH", "scanner": "semgrep"}
            )
            return {
                "status": ScanJobStatus.UNAVAILABLE.value,
                "message": "Semgrep executable was not found on the system PATH or configured SEMGREP_PATH.",
                "result_location": result_dir
            }

        scan_dir = get_scan_storage_dir(assessment_id, job_id)
        report_file = scan_dir / "semgrep_output.json"
        timeout = config.get("timeout", 180) if config else 180
        target_path = target if os.path.exists(target) else "./"

        cmd = [
            exec_path,
            "scan",
            "--config=auto",
            f"--json-output={str(report_file)}",
            "--quiet",
            target_path
        ]

        proc_result = await run_safe_process(cmd_args=cmd, cwd=str(scan_dir), timeout=timeout)

        raw_data = None
        if report_file.is_file():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception:
                raw_data = {"raw_stdout": proc_result.stdout}

        final_status = ScanJobStatus.COMPLETED.value if proc_result.exit_code in [0, 1] else ScanJobStatus.FAILED.value
        if proc_result.timed_out:
            final_status = ScanJobStatus.TIMEOUT.value

        result_dir = store_scan_job_results(
            assessment_id=assessment_id,
            scan_job_id=job_id,
            scanner_name=self.name(),
            target=target,
            status=final_status,
            exit_code=proc_result.exit_code,
            duration_seconds=proc_result.duration_seconds,
            stdout=proc_result.stdout,
            stderr=proc_result.stderr,
            raw_json_data=raw_data
        )

        return {
            "status": final_status,
            "exit_code": proc_result.exit_code,
            "duration_seconds": proc_result.duration_seconds,
            "result_location": result_dir
        }

    def cancel(self, job_id: int) -> bool:
        return True

    def parse_results(self, result_location: Optional[str]) -> List[Dict[str, Any]]:
        return []


class SCAScannerAdapter(ScannerAdapter):
    """Software Composition Analysis (OWASP Dependency-Check) Adapter."""

    def name(self) -> str:
        return "Dependency Check (SCA)"

    def engine_type(self) -> ScannerEngineType:
        return ScannerEngineType.SCA

    def is_available(self) -> tuple[bool, Optional[str]]:
        return check_tool_available("dependency-check.bat", settings.dependency_check_path) or check_tool_available("dependency-check.sh", settings.dependency_check_path) or check_tool_available("dependency-check", settings.dependency_check_path)

    def validate_config(self, config: Optional[Dict[str, Any]]) -> bool:
        return True

    def prepare(self, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "engine": "sca",
            "target_path": target,
            "timeout": config.get("timeout", 240) if config else 240,
            "prepared_at": datetime.utcnow().isoformat()
        }

    async def execute(self, job_id: int, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        available, exec_path = self.is_available()
        if not available:
            logger.warning(f"Dependency-Check executable not found for job {job_id}")
            result_dir = store_scan_job_results(
                assessment_id=assessment_id,
                scan_job_id=job_id,
                scanner_name=self.name(),
                target=target,
                status=ScanJobStatus.UNAVAILABLE.value,
                exit_code=-1,
                duration_seconds=0,
                stdout="",
                stderr="OWASP Dependency-Check was not found on system PATH or configured DEPENDENCY_CHECK_PATH.",
                raw_json_data={"error": "Dependency-Check not installed", "scanner": "sca"}
            )
            return {
                "status": ScanJobStatus.UNAVAILABLE.value,
                "message": "OWASP Dependency-Check was not found on system PATH or configured DEPENDENCY_CHECK_PATH.",
                "result_location": result_dir
            }

        scan_dir = get_scan_storage_dir(assessment_id, job_id)
        report_file = scan_dir / "dependency-check-report.json"
        timeout = config.get("timeout", 300) if config else 300
        target_path = target if os.path.exists(target) else "./"

        cmd = [
            exec_path,
            "--project", f"AegisScan-{assessment_id}",
            "--scan", target_path,
            "--format", "JSON",
            "--out", str(scan_dir)
        ]

        proc_result = await run_safe_process(cmd_args=cmd, cwd=str(scan_dir), timeout=timeout)

        raw_data = None
        if report_file.is_file():
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception:
                raw_data = {"raw_stdout": proc_result.stdout}

        final_status = ScanJobStatus.COMPLETED.value if proc_result.exit_code == 0 else ScanJobStatus.FAILED.value
        if proc_result.timed_out:
            final_status = ScanJobStatus.TIMEOUT.value

        result_dir = store_scan_job_results(
            assessment_id=assessment_id,
            scan_job_id=job_id,
            scanner_name=self.name(),
            target=target,
            status=final_status,
            exit_code=proc_result.exit_code,
            duration_seconds=proc_result.duration_seconds,
            stdout=proc_result.stdout,
            stderr=proc_result.stderr,
            raw_json_data=raw_data
        )

        return {
            "status": final_status,
            "exit_code": proc_result.exit_code,
            "duration_seconds": proc_result.duration_seconds,
            "result_location": result_dir
        }

    def cancel(self, job_id: int) -> bool:
        return True

    def parse_results(self, result_location: Optional[str]) -> List[Dict[str, Any]]:
        return []


class CustomChecksScannerAdapter(ScannerAdapter):
    """AegisScan Native Custom Security Rules Adapter."""

    def name(self) -> str:
        return "AegisScan Custom Rules"

    def engine_type(self) -> ScannerEngineType:
        return ScannerEngineType.CUSTOM

    def is_available(self) -> tuple[bool, Optional[str]]:
        # Native python engine is always available
        return True, "built-in"

    def validate_config(self, config: Optional[Dict[str, Any]]) -> bool:
        return True

    def prepare(self, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "engine": "custom_checks",
            "target": target,
            "timeout": config.get("timeout", 30) if config else 30,
            "prepared_at": datetime.utcnow().isoformat()
        }

    async def execute(self, job_id: int, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = time.time()
        timeout = config.get("timeout", 30) if config else 30

        try:
            results_data = await execute_custom_security_checks(target_url=target, timeout=timeout)
            duration = round(time.time() - start_time, 2)

            result_dir = store_scan_job_results(
                assessment_id=assessment_id,
                scan_job_id=job_id,
                scanner_name=self.name(),
                target=target,
                status=ScanJobStatus.COMPLETED.value,
                exit_code=0,
                duration_seconds=duration,
                stdout=f"Executed {results_data.get('total_checks_run', 0)} custom security checks.",
                stderr="",
                raw_json_data=results_data
            )

            return {
                "status": ScanJobStatus.COMPLETED.value,
                "exit_code": 0,
                "duration_seconds": duration,
                "result_location": result_dir,
                "checks_run": results_data.get("total_checks_run", 0),
                "issues_detected": results_data.get("issues_detected", 0)
            }

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            result_dir = store_scan_job_results(
                assessment_id=assessment_id,
                scan_job_id=job_id,
                scanner_name=self.name(),
                target=target,
                status=ScanJobStatus.FAILED.value,
                exit_code=-1,
                duration_seconds=duration,
                stdout="",
                stderr=str(e),
                raw_json_data={"error": str(e)}
            )
            return {
                "status": ScanJobStatus.FAILED.value,
                "exit_code": -1,
                "duration_seconds": duration,
                "result_location": result_dir,
                "error": str(e)
            }

    def cancel(self, job_id: int) -> bool:
        return True

    def parse_results(self, result_location: Optional[str]) -> List[Dict[str, Any]]:
        return []


# Adapter Registry
_ADAPTER_REGISTRY: Dict[ScannerEngineType, ScannerAdapter] = {
    ScannerEngineType.ZAP: ZAPScannerAdapter(),
    ScannerEngineType.NUCLEI: NucleiScannerAdapter(),
    ScannerEngineType.SEMGREP: SemgrepScannerAdapter(),
    ScannerEngineType.SCA: SCAScannerAdapter(),
    ScannerEngineType.CUSTOM: CustomChecksScannerAdapter()
}


def get_scanner_adapter(scanner_type: ScannerEngineType) -> ScannerAdapter:
    """
    Retrieve scanner adapter instance by type.
    """
    adapter = _ADAPTER_REGISTRY.get(scanner_type)
    if not adapter:
        raise ValueError(f"No scanner adapter registered for engine type: {scanner_type}")
    return adapter


def list_available_scanners() -> List[Dict[str, Any]]:
    """
    Query the installation and availability status of all registered scanner engines.
    """
    status_list = []
    for engine_type, adapter in _ADAPTER_REGISTRY.items():
        available, path = adapter.is_available()
        status_list.append({
            "scanner": engine_type.value,
            "name": adapter.name(),
            "available": available,
            "resolved_path": path,
            "type": "dast" if engine_type in [ScannerEngineType.ZAP, ScannerEngineType.NUCLEI] else ("sast" if engine_type == ScannerEngineType.SEMGREP else ("sca" if engine_type == ScannerEngineType.SCA else "custom"))
        })
    return status_list
