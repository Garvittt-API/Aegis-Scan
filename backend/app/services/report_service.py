"""Evidence-backed report dataset and HTML/PDF rendering."""
import hashlib
import html
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.assessment import Assessment
from app.models.finding import Finding, Severity, VerificationStatus
from app.models.remediation import Remediation, RemediationStatus
from app.models.report import Report, ReportFormat, ReportStatus
from app.models.scan_job import ScanJob


def redact(value: Any) -> str:
    """Redact secrets for presentation without changing stored evidence."""
    text = str(value or "")
    patterns = [
        (r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+", r"\1[REDACTED]"),
        (r"(?i)(api[-_ ]?key\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
        (r"(?i)(password\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
        (r"(?i)(cookie\s*:\s*)[^\s,;]+", r"\1[REDACTED]"),
        (r"(?i)(set-cookie\s*:\s*)[^\s,;]+", r"\1[REDACTED]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def _enum(value):
    return value.value if hasattr(value, "value") else value


def build_report_dataset(db: Session, assessment: Assessment) -> dict[str, Any]:
    findings = db.query(Finding).filter(Finding.assessment_id == assessment.id).order_by(Finding.severity.desc(), Finding.id.asc()).all()
    jobs = db.query(ScanJob).filter(ScanJob.assessment_id == assessment.id).order_by(ScanJob.id.asc()).all()
    remediation_by_finding = {
        item.finding_id: item for item in db.query(Remediation).join(Finding).filter(Finding.assessment_id == assessment.id).all()
    }
    severity_counts = {level.value: sum(1 for item in findings if item.severity == level) for level in Severity}
    verification_counts = {state.value: sum(1 for item in findings if item.verification_status == state) for state in VerificationStatus}
    remediation_counts = {state.value: sum(1 for state_item in RemediationStatus if False) for state in RemediationStatus}
    remediation_counts = {state.value: sum(1 for item in remediation_by_finding.values() if item.status == state) for state in RemediationStatus}
    tool_status = []
    for job in jobs:
        tool_status.append({
            "component": job.scanner.value,
            "status": job.status.value.upper(),
            "evidence": bool(job.result_location),
            "run_id": job.id,
        })
    finding_rows = []
    for item in findings:
        remediation = remediation_by_finding.get(item.id)
        finding_rows.append({
            "id": item.id,
            "title": redact(item.title),
            "severity": _enum(item.severity),
            "confidence": item.confidence,
            "verification_status": _enum(item.verification_status),
            "risk_score": item.risk_score,
            "priority": _enum(item.priority),
            "risk_explanation": redact(item.risk_explanation),
            "category": _enum(item.category),
            "cwe": redact(item.cwe),
            "cvss": item.cvss_score,
            "endpoint": redact(item.endpoint),
            "method": item.method,
            "parameter": redact(item.parameter),
            "scanner": redact(item.scanner),
            "status": _enum(item.status),
            "evidence": redact(item.evidence),
            "raw_evidence_reference": redact(item.raw_output),
            "verification_reason": redact(item.verification_reason),
            "reproducibility": item.reproducibility,
            "remediation": {
                "status": _enum(remediation.status),
                "recommended_action": redact(remediation.recommended_action),
                "technical_steps": redact(remediation.technical_steps),
                "verification_steps": redact(remediation.verification_steps),
            } if remediation else None,
        })
    target = assessment.target
    return {
        "project": "AegisScan",
        "report_version": "1.0",
        "assessment": {
            "id": assessment.id,
            "name": assessment.name,
            "target": target.name if target else None,
            "target_type": _enum(target.target_type) if target else None,
            "target_url": assessment.target_url or (target.base_url if target else None),
            "environment": _enum(assessment.environment),
            "authorization_confirmed": assessment.authorization_confirmed,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "scope": assessment.scope,
        },
        "summary": {
            "findings": len(findings),
            "severity": severity_counts,
            "verification": verification_counts,
            "remediation": remediation_counts,
        },
        "tools": tool_status,
        "findings": finding_rows,
        "methodology": ["Target configuration", "Attack surface discovery", "Scan planning", "Scanner execution", "Evidence collection", "Finding normalization and correlation", "Verification", "Risk analysis", "Remediation analysis"],
        "limitations": ["Results depend on the checks executed.", "Unavailable or failed scanners reduce coverage.", "Automated assessment cannot guarantee absence of vulnerabilities.", "Unverified findings require further investigation.", "Raw evidence is referenced, not reproduced wholesale, for privacy and size control."],
    }


def render_html(dataset: dict[str, Any]) -> str:
    summary = dataset["summary"]
    assessment = dataset["assessment"]
    if summary["findings"]:
        finding_intro = "The assessment identified findings requiring review."
    else:
        finding_intro = "No security findings were produced by the executed assessment."
    severity_rows = "".join(f"<tr><th>{html.escape(key.title())}</th><td>{value}</td></tr>" for key, value in summary["severity"].items())
    verification_rows = "".join(f"<tr><th>{html.escape(key.replace('_', ' ').title())}</th><td>{value}</td></tr>" for key, value in summary["verification"].items())
    tool_rows = "".join(f"<tr><td>{html.escape(str(tool['component']))}</td><td>{html.escape(str(tool['status']))}</td><td>{'Yes' if tool['evidence'] else 'No'}</td></tr>" for tool in dataset["tools"])
    findings_html = []
    for finding in dataset["findings"]:
        remediation = finding["remediation"]
        findings_html.append(f"""<article class='finding'><h3>Finding #{finding['id']}: {html.escape(str(finding['title']))}</h3><table><tr><th>Severity</th><td>{html.escape(str(finding['severity']))}</td><th>Confidence</th><td>{finding['confidence'] if finding['confidence'] is not None else 'Not available'}</td></tr><tr><th>Verification</th><td>{html.escape(str(finding['verification_status']))}</td><th>Risk</th><td>{finding['risk_score'] if finding['risk_score'] is not None else 'Risk not calculated'}</td></tr><tr><th>Priority</th><td>{html.escape(str(finding['priority'] or 'Not available'))}</td><th>Category</th><td>{html.escape(str(finding['category']))}</td></tr></table><h4>Evidence</h4><p>{html.escape(str(finding['evidence'] or 'Evidence not available.'))}</p><p><strong>Raw evidence reference:</strong> {html.escape(str(finding['raw_evidence_reference'] or 'Not available'))}</p><h4>Remediation</h4><p>{html.escape(str(remediation['recommended_action'] if remediation else 'No remediation record exists.'))}</p><p><strong>Status:</strong> {html.escape(str(remediation['status'] if remediation else 'Not available'))}</p></article>""")
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>AegisScan Security Assessment Report</title><style>body{{font-family:Arial,sans-serif;color:#17202a;max-width:1000px;margin:0 auto;padding:32px;line-height:1.45}}h1{{color:#123b5d}}h2{{border-bottom:2px solid #dce6ee;padding-bottom:6px;margin-top:32px}}table{{border-collapse:collapse;width:100%;margin:10px 0 20px}}th,td{{border:1px solid #dce6ee;padding:8px;text-align:left}}th{{background:#f1f5f8}}.finding{{border:1px solid #c8d6e0;padding:18px;margin:20px 0;page-break-inside:avoid}}.muted{{color:#5f6f7a}}@media print{{body{{padding:0}}h2{{page-break-after:avoid}}}}</style></head><body><h1>AegisScan Security Assessment Report</h1><p class='muted'>Report version {dataset['report_version']} | Generated {datetime.utcnow().isoformat()} UTC</p><h2>Executive Summary</h2><p>{html.escape(finding_intro)}</p><p><strong>Assessment:</strong> {html.escape(str(assessment['name']))} (#{assessment['id']})</p><p><strong>Target:</strong> {html.escape(str(assessment['target'] or assessment['target_url'] or 'Not available'))}</p><p><strong>Authorization confirmed:</strong> {assessment['authorization_confirmed']}</p><h3>Severity Distribution</h3><table>{severity_rows}</table><h3>Verification Distribution</h3><table>{verification_rows}</table><h2>Methodology</h2><ol>{''.join(f'<li>{html.escape(step)}</li>' for step in dataset['methodology'])}</ol><h2>Tool Execution</h2><table><tr><th>Component</th><th>Status</th><th>Evidence</th></tr>{tool_rows or '<tr><td colspan=3>Not assessed</td></tr>'}</table><h2>Findings</h2>{''.join(findings_html) or '<p>No security findings were produced by the executed assessment.</p>'}<h2>Remediation Summary</h2><table>{''.join(f'<tr><th>{html.escape(key.replace("_", " ").title())}</th><td>{value}</td></tr>' for key, value in summary['remediation'].items())}</table><h2>Limitations</h2><ul>{''.join(f'<li>{html.escape(item)}</li>' for item in dataset['limitations'])}</ul></body></html>"""


def generate_report(db: Session, assessment_id: int, report_format: ReportFormat) -> Report:
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise ValueError("Assessment not found")
    report = Report(assessment_id=assessment_id, format=report_format, title=f"AegisScan Assessment {assessment_id}", status=ReportStatus.GENERATING, generated_by="AegisScan", generated_at=datetime.utcnow())
    db.add(report); db.commit(); db.refresh(report)
    start = monotonic()
    try:
        dataset = build_report_dataset(db, assessment)
        content = render_html(dataset)
        report_dir = Path(settings.reports_dir or Path("./reports")) / "assessments" / str(assessment_id) / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        if report_format == ReportFormat.HTML:
            path = report_dir / f"aegisscan-assessment-{assessment_id}-{report.id}.html"
            path.write_text(content, encoding="utf-8")
        elif report_format == ReportFormat.PDF:
            if importlib.util.find_spec("weasyprint"):
                from weasyprint import HTML
                path = report_dir / f"aegisscan-assessment-{assessment_id}-{report.id}.pdf"
                HTML(string=content).write_pdf(str(path))
            elif importlib.util.find_spec("reportlab"):
                report.error = "PDF renderer available only through ReportLab integration; HTML report remains available."
                report.status = ReportStatus.FAILED
                db.commit(); return report
            else:
                report.error = "No supported PDF renderer is installed; generate HTML or install WeasyPrint/ReportLab."
                report.status = ReportStatus.FAILED
                db.commit(); return report
        else:
            path = report_dir / f"aegisscan-assessment-{assessment_id}-{report.id}.json"
            path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
        report.file_path = str(path)
        report.file_size_bytes = path.stat().st_size
        report.content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        report.status = ReportStatus.COMPLETED
        report.completed_at = datetime.utcnow()
        db.commit(); db.refresh(report)
        return report
    except Exception as exc:
        report.status = ReportStatus.FAILED
        report.error = str(exc)
        db.commit(); db.refresh(report)
        return report
