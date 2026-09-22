"""Normalize, fingerprint, deduplicate, and persist scanner findings."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.finding import Finding, FindingCategory, Severity, VerificationStatus, FindingStatus
from app.models.scan_job import ScanJob
from app.services.findings.parsers import PARSERS
from app.services.findings.risk import calculate_risk, determine_exposure


def fingerprint(candidate: Dict[str, Any]) -> str:
    parts = [
        str(candidate.get("category", "other")).strip().lower(),
        str(candidate.get("endpoint") or candidate.get("source_file") or "").strip().lower(),
        str(candidate.get("method") or "").strip().lower(),
        str(candidate.get("parameter") or "").strip().lower(),
        str(candidate.get("cwe") or candidate.get("title") or "").strip().lower(),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


class FindingService:
    """Central Phase 5 finding ingestion service."""

    @staticmethod
    def process_scan_result(db: Session, job: ScanJob) -> List[Finding]:
        if not job.result_location:
            return []
        result_path = Path(job.result_location) / "result.json"
        if not result_path.exists():
            return []
        try:
            with result_path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
            parser = PARSERS.get(job.scanner.value)
            if not parser:
                return []
            candidates = parser(raw)
        except Exception as exc:
            job.logs = (job.logs or []) + [{
                "time": datetime.utcnow().isoformat(),
                "level": "ERROR",
                "msg": f"Finding parser failed: {exc}",
            }]
            db.commit()
            return []

        findings = []
        for candidate in candidates:
            current = FindingService._upsert(db, job, candidate, result_path)
            if current:
                findings.append(current)
        db.commit()
        return findings

    @staticmethod
    def _upsert(db: Session, job: ScanJob, candidate: Dict[str, Any], result_path: Path) -> Finding:
        fp = fingerprint(candidate)
        existing = db.query(Finding).filter(
            Finding.assessment_id == job.assessment_id,
            Finding.fingerprint == fp,
            Finding.duplicate_of.is_(None),
        ).first()
        scanner = job.scanner.value
        if existing:
            sources = json.loads(existing.source_scanners or "[]")
            if scanner not in sources:
                sources.append(scanner)
                existing.source_scanners = json.dumps(sorted(sources))
            raw_paths = [path for path in (existing.raw_output or "").split("\n") if path]
            if str(result_path) not in raw_paths:
                raw_paths.append(str(result_path))
                existing.raw_output = "\n".join(raw_paths)
            existing.last_seen = datetime.utcnow()
            return existing

        severity = Severity(candidate.get("severity", "informational"))
        category_value = candidate.get("category", FindingCategory.OTHER.value)
        try:
            category = FindingCategory(category_value)
        except ValueError:
            category = FindingCategory.OTHER
        finding = Finding(
            assessment_id=job.assessment_id,
            scan_job_id=job.id,
            title=str(candidate.get("title") or "Untitled finding"),
            description=candidate.get("description"),
            severity=severity,
            confidence=float(candidate.get("confidence", 0.5)),
            category=category,
            scanner=scanner,
            scanner_id=candidate.get("scanner_id"),
            source_scanners=json.dumps([scanner]),
            cwe=candidate.get("cwe"),
            endpoint=candidate.get("endpoint"),
            method=candidate.get("method"),
            parameter=candidate.get("parameter"),
            source_file=candidate.get("source_file"),
            source_line=candidate.get("source_line"),
            evidence=json.dumps(candidate.get("evidence")) if isinstance(candidate.get("evidence"), (dict, list)) else candidate.get("evidence"),
            evidence_type="scanner_output",
            raw_output=str(result_path),
            verification_status=VerificationStatus.UNVERIFIED,
            status=FindingStatus.OPEN,
            remediation=candidate.get("remediation"),
            references=candidate.get("references"),
            fingerprint=fp,
        )
        finding.exposure = determine_exposure(finding.endpoint)
        risk = calculate_risk(finding)
        finding.risk_score = risk["score"]
        finding.risk_level = risk["level"]
        finding.priority = risk["level"]
        finding.risk_explanation = risk["explanation"]
        db.add(finding)
        return finding
