"""Local and CI-friendly AegisScan command line interface."""
import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from app.core.database import SessionLocal
from app.models.assessment import Assessment, AssessmentStatus
from app.models.finding import Finding
from app.models.scan_job import ScanJob
from app.services.analytics_service import comparison, scanner_coverage
from app.services.ci_policy import EXIT_CONFIGURATION, EXIT_POLICY_FAILED, EXIT_RUNTIME, EXIT_SUCCESS, evaluate_policy, load_policy
from app.services.report_service import generate_report
from app.models.report import ReportFormat
from app.services.scan_orchestrator import ScanOrchestrator, ScanPlanner
from app.utils.security_validation import validate_url

@click.group()
def cli():
    """AegisScan local and CI security assessment commands."""

console = Console()


def _safe_output_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sarif(findings: list[Finding]) -> dict:
    results = []
    for finding in findings:
        level = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "informational": "note"}.get(finding.severity.value, "note")
        result = {
            "ruleId": finding.fingerprint or f"finding-{finding.id}",
            "level": level,
            "message": {"text": finding.title},
            "properties": {"severity": finding.severity.value, "confidence": finding.confidence, "verification": finding.verification_status.value, "fingerprint": finding.fingerprint},
        }
        if finding.endpoint:
            result["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": finding.endpoint}}}]
        elif finding.source_file:
            location = {"physicalLocation": {"artifactLocation": {"uri": finding.source_file}}}
            if finding.source_line:
                location["physicalLocation"]["region"] = {"startLine": finding.source_line}
            result["locations"] = [location]
        results.append(result)
    return {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "AegisScan", "informationUri": "https://github.com/AegisScan"}}, "results": results}]}


def _json_result(assessment_id: int, findings: list[Finding], policy_result: dict, scanner_items: list[dict], baseline_id: Optional[int]) -> dict:
    counts = {level: sum(1 for finding in findings if finding.severity.value == level) for level in ("critical", "high", "medium", "low", "informational")}
    return {
        "assessment_id": assessment_id,
        "status": policy_result["status"],
        "findings": len(findings),
        **counts,
        "policy": policy_result,
        "baseline_assessment_id": baseline_id,
        "scanner_coverage": scanner_items,
    }


def _print_result(result: dict) -> None:
    table = Table(title="AegisScan CI Assessment")
    table.add_column("Metric"); table.add_column("Value")
    for key in ("assessment_id", "findings", "critical", "high", "medium", "low", "informational"):
        table.add_row(key.replace("_", " ").title(), str(result[key]))
    table.add_row("Policy", result["status"])
    console.print(table)
    console.print(result["policy"]["reason"])


@cli.command()
@click.option("--target", default="", help="Explicit authorized target URL or source path.")
@click.option("--policy", default=None, help="YAML security policy file.")
@click.option("--output", default="artifacts", show_default=True, help="Local artifact directory.")
@click.option("--format", "formats", default="json,sarif", show_default=True, help="Comma-separated formats: json,sarif,html,pdf.")
@click.option("--baseline", type=int, default=None, help="Existing assessment ID to use as baseline.")
@click.option("--source-path", default=None, help="Authorized source-code path.")
def ci(
    target: str,
    policy: Optional[str],
    output: str,
    formats: str,
    baseline: Optional[int],
    source_path: Optional[str],
):
    """Execute a real AegisScan assessment and evaluate a deterministic CI policy."""
    try:
        policy_data = load_policy(policy)
        output_dir = _safe_output_dir(output)
        db = SessionLocal()
        try:
            modules = policy_data.get("modules") or {"dast": True, "nuclei": True, "sast": bool(source_path), "sca": bool(source_path), "custom_checks": True}
            if not target:
                raise ValueError("--target is required")
            target_url = target if target.startswith(("http://", "https://")) else None
            if target_url:
                valid, error = validate_url(target_url)
                if not valid:
                    raise ValueError(error)
            elif not source_path:
                candidate_path = Path(target).expanduser().resolve()
                if candidate_path.exists():
                    source_path = str(candidate_path)
                else:
                    raise ValueError("Target must be an HTTP(S) URL or an existing source path")
            assessment = Assessment(name="AegisScan CI Assessment", target_url=target_url, source_path=source_path, authorization_confirmed=True, modules=modules, scope=policy_data.get("scope") or {})
            db.add(assessment); db.commit(); db.refresh(assessment)
            jobs = ScanPlanner.generate_plan(db, assessment)
            results = asyncio.run(ScanOrchestrator.run_all_jobs(db, assessment.id))
            db.refresh(assessment)
            findings = db.query(Finding).filter_by(assessment_id=assessment.id).all()
            scanner_items = scanner_coverage(db, assessment.id)
            baseline_id = baseline
            if baseline_id is None and (policy_data.get("baseline") or {}).get("mode") in {"previous", "previous_successful"}:
                previous = db.query(Assessment).filter(Assessment.id != assessment.id, Assessment.status == AssessmentStatus.COMPLETED).order_by(Assessment.created_at.desc()).first()
                baseline_id = previous.id if previous else None
            comparison_result = None
            if baseline_id is not None:
                try:
                    comparison_result = comparison(db, baseline_id, assessment.id)
                except ValueError:
                    raise ValueError("Configured baseline assessment was not found")
            policy_result = evaluate_policy(policy_data, findings, comparison_result, scanner_items)
            result = _json_result(assessment.id, findings, policy_result, scanner_items, baseline_id)
            requested = {item.strip().lower() for item in formats.split(",") if item.strip()}
            if "json" in requested:
                (output_dir / "aegisscan-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            if "sarif" in requested:
                (output_dir / "aegisscan-results.sarif").write_text(json.dumps(_sarif(findings), indent=2), encoding="utf-8")
            if "html" in requested:
                report = generate_report(db, assessment.id, ReportFormat.HTML)
                if report.status.value == "completed" and report.file_path:
                    shutil.copyfile(report.file_path, output_dir / "aegisscan-report.html")
            if "pdf" in requested:
                report = generate_report(db, assessment.id, ReportFormat.PDF)
                if report.status.value == "completed" and report.file_path:
                    shutil.copyfile(report.file_path, output_dir / "aegisscan-report.pdf")
                else:
                    result.setdefault("artifacts", {})["pdf"] = report.error or "PDF generation failed"
            _print_result(result)
            if policy_result["status"] == "FAIL":
                raise click.exceptions.Exit(EXIT_POLICY_FAILED)
            if policy_result["status"] in {"UNKNOWN", "WARN"}:
                raise click.exceptions.Exit(EXIT_SUCCESS)
            raise click.exceptions.Exit(EXIT_SUCCESS)
        finally:
            db.close()
    except click.exceptions.Exit:
        raise
    except ValueError as exc:
        console.print(f"Configuration error: {exc}", style="red")
        raise click.exceptions.Exit(EXIT_CONFIGURATION)
    except Exception as exc:
        console.print(f"Runtime error: {exc}", style="red")
        raise click.exceptions.Exit(EXIT_RUNTIME)


if __name__ == "__main__":
    cli()
