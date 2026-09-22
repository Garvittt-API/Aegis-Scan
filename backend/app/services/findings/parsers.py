"""Evidence-preserving parsers for supported scanner result formats."""

from typing import Any, Dict, List


def _severity(value: Any) -> str:
    value = str(value or "informational").lower()
    for level in ("critical", "high", "medium", "low", "informational", "info"):
        if level in value:
            return "informational" if level == "info" else level
    if value in {"critical", "high", "medium", "low", "informational"}:
        return value
    if value in {"error", "warning"}:
        return "medium" if value == "warning" else "high"
    return "informational"


def _refs(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _confidence(value: Any) -> float:
    if isinstance(value, str) and not value.replace(".", "", 1).isdigit():
        return {"high": 0.9, "medium": 0.6, "low": 0.3}.get(value.lower(), 0.5)
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.5
    return numeric / 100 if numeric > 1 else numeric


def parse_zap(data: Any) -> List[Dict[str, Any]]:
    alerts = data.get("site", []) if isinstance(data, dict) else data
    if isinstance(alerts, dict):
        alerts = [alerts]
    results = []
    for site in alerts or []:
        for alert in site.get("alerts", [site]) if isinstance(site, dict) else []:
            if not isinstance(alert, dict):
                continue
            results.append({
                "title": alert.get("alert") or alert.get("name") or "ZAP alert",
                "description": alert.get("desc") or alert.get("description"),
                "severity": _severity(alert.get("riskdesc", alert.get("risk"))),
                "confidence": min(_confidence(alert.get("confidence", 50)), 1.0),
                "scanner_id": alert.get("pluginid"),
                "endpoint": alert.get("uri") or site.get("@name") if isinstance(site, dict) else None,
                "method": alert.get("method"),
                "parameter": alert.get("param"),
                "evidence": alert.get("evidence") or alert.get("attack"),
                "remediation": alert.get("solution"),
                "references": _refs(alert.get("reference")),
                "cwe": alert.get("cweid"),
                "category": "configuration",
            })
    return results


def parse_nuclei(data: Any) -> List[Dict[str, Any]]:
    records = data if isinstance(data, list) else [data]
    results = []
    for record in records:
        if not isinstance(record, dict) or record.get("error"):
            continue
        info = record.get("info") or {}
        results.append({
            "title": info.get("name") or record.get("template-id") or "Nuclei finding",
            "description": info.get("description"),
            "severity": _severity(info.get("severity")),
            "confidence": 0.8,
            "scanner_id": record.get("template-id"),
            "endpoint": record.get("matched-at") or record.get("host"),
            "evidence": record.get("matcher-name") or record.get("extracted-results"),
            "references": _refs(info.get("reference")),
            "category": "configuration",
        })
    return results


def parse_semgrep(data: Any) -> List[Dict[str, Any]]:
    results = []
    for record in (data or {}).get("results", []) if isinstance(data, dict) else []:
        if not isinstance(record, dict):
            continue
        extra = record.get("extra") or {}
        metadata = extra.get("metadata") or {}
        start = record.get("start") or {}
        path = record.get("path")
        results.append({
            "title": extra.get("message") or record.get("check_id") or "Semgrep finding",
            "description": extra.get("message"),
            "severity": _severity(metadata.get("severity") or extra.get("severity")),
            "confidence": 0.8,
            "scanner_id": record.get("check_id"),
            "source_file": path,
            "source_line": start.get("line"),
            "evidence": extra.get("lines") or extra.get("metavars"),
            "cwe": _refs(metadata.get("cwe")),
            "references": _refs(metadata.get("references")),
            "category": "secrets" if "secret" in str(record.get("check_id", "")).lower() else "input_validation",
        })
    return results


def parse_dependency_check(data: Any) -> List[Dict[str, Any]]:
    results = []
    for dependency in (data or {}).get("dependencies", []) if isinstance(data, dict) else []:
        for vulnerability in dependency.get("vulnerabilities", []) or []:
            if not isinstance(vulnerability, dict):
                continue
            results.append({
                "title": vulnerability.get("name") or vulnerability.get("source") or "Dependency vulnerability",
                "description": vulnerability.get("description"),
                "severity": _severity(vulnerability.get("severity")),
                "confidence": 0.9,
                "scanner_id": vulnerability.get("name"),
                "source_file": dependency.get("filePath"),
                "evidence": dependency.get("fileName") or dependency.get("packagePath"),
                "references": _refs(vulnerability.get("references")),
                "category": "dependency",
            })
    return results


def parse_custom(data: Any) -> List[Dict[str, Any]]:
    records = data.get("results", []) if isinstance(data, dict) else []
    results = []
    for record in records:
        if not isinstance(record, dict) or record.get("status") not in {"detected", "potential"}:
            continue
        results.append({
            "title": record.get("name") or record.get("check_id") or "Custom security check",
            "description": record.get("details"),
            "severity": _severity(record.get("severity")),
            "confidence": 0.75 if record.get("status") == "detected" else 0.5,
            "scanner_id": record.get("check_id"),
            "endpoint": data.get("target") if isinstance(data, dict) else None,
            "evidence": record.get("evidence"),
            "remediation": record.get("remediation"),
            "category": "configuration",
        })
    return results


PARSERS = {
    "zap": parse_zap,
    "nuclei": parse_nuclei,
    "semgrep": parse_semgrep,
    "sca": parse_dependency_check,
    "custom": parse_custom,
}
