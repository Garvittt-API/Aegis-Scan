"""Deterministic CI policy parsing and evaluation."""
from pathlib import Path
from typing import Any
import yaml

from app.models.finding import FindingStatus, VerificationStatus

EXIT_SUCCESS = 0
EXIT_POLICY_FAILED = 1
EXIT_CONFIGURATION = 2
EXIT_RUNTIME = 3


def load_policy(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    policy_path = Path(path).resolve()
    if not policy_path.is_file():
        raise ValueError(f"Policy file not found: {policy_path}")
    try:
        data = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid policy YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Policy root must be a mapping")
    return data


def _rule(name: str, status: str, actual: Any = None, threshold: Any = None, reason: str = "") -> dict[str, Any]:
    return {"rule": name, "status": status, "actual": actual, "threshold": threshold, "reason": reason}


def evaluate_policy(policy: dict[str, Any], findings: list, comparison: dict[str, Any] | None = None, scanner_items: list[dict] | None = None) -> dict[str, Any]:
    rules = []
    failures = []
    warnings = []
    limits = policy.get("max_findings", {}) or {}
    severity_counts = {level: sum(1 for finding in findings if getattr(finding.severity, "value", finding.severity) == level) for level in ("critical", "high", "medium", "low", "informational")}

    for level, threshold in limits.items():
        if level not in severity_counts or not isinstance(threshold, int) or threshold < 0:
            rules.append(_rule(f"max_{level}_findings", "UNKNOWN", severity_counts.get(level), threshold, "Invalid or unsupported severity threshold."))
            continue
        actual = severity_counts[level]
        status = "FAIL" if actual > threshold else "PASS"
        reason = f"{actual} {level} findings exceed configured threshold of {threshold}." if status == "FAIL" else f"{actual} {level} findings are within threshold {threshold}."
        rules.append(_rule(f"max_{level}_findings", status, actual, threshold, reason))
        (failures if status == "FAIL" else []).append(rules[-1])

    fail_on = set(policy.get("fail_on", []) or [])
    for level in sorted(fail_on):
        if level not in severity_counts:
            rules.append(_rule(f"fail_on_{level}", "UNKNOWN", None, level, "Unsupported severity policy."))
            continue
        actual = severity_counts[level]
        status = "FAIL" if actual > 0 else "PASS"
        result = _rule(f"fail_on_{level}", status, actual, 0, f"{actual} {level} findings detected." if actual else f"No {level} findings detected.")
        rules.append(result)
        (failures if status == "FAIL" else []).append(result)

    if policy.get("fail_on_unverified", False):
        actual = sum(1 for finding in findings if finding.verification_status == VerificationStatus.UNVERIFIED)
        result = _rule("fail_on_unverified", "FAIL" if actual else "PASS", actual, 0, f"{actual} unverified findings detected.")
        rules.append(result)
        (failures if result["status"] == "FAIL" else []).append(result)

    if policy.get("verification_required", False) and not policy.get("fail_on_unverified", False):
        actual = sum(1 for finding in findings if finding.verification_status == VerificationStatus.UNVERIFIED)
        result = _rule("verification_required", "FAIL" if actual else "PASS", actual, 0, f"{actual} findings remain unverified." if actual else "All findings have a verification state other than unverified.")
        rules.append(result)
        (failures if result["status"] == "FAIL" else []).append(result)

    warning_limit = policy.get("warn_on_unverified")
    if warning_limit is not None:
        actual = sum(1 for finding in findings if finding.verification_status == VerificationStatus.UNVERIFIED)
        result = _rule("warn_on_unverified", "WARN" if actual > warning_limit else "PASS", actual, warning_limit, f"{actual} unverified findings exceed warning threshold {warning_limit}." if actual > warning_limit else "Unverified findings are within warning threshold.")
        rules.append(result)
        (warnings if result["status"] == "WARN" else []).append(result)

    if policy.get("fail_on_new_findings", False):
        if comparison is None:
            result = _rule("fail_on_new_findings", "UNKNOWN", None, 0, "Baseline unavailable.")
        else:
            result = _rule("fail_on_new_findings", "FAIL" if comparison["new"] else "PASS", comparison["new"], 0, f"{comparison['new']} new findings detected." if comparison["new"] else "No new findings detected.")
        rules.append(result)
        (failures if result["status"] == "FAIL" else []).append(result)

    if policy.get("fail_on_reopened_findings", False):
        if comparison is None:
            result = _rule("fail_on_reopened_findings", "UNKNOWN", None, 0, "Baseline unavailable.")
        else:
            result = _rule("fail_on_reopened_findings", "FAIL" if comparison["reopened"] else "PASS", comparison["reopened"], 0, f"{comparison['reopened']} reopened findings detected." if comparison["reopened"] else "No reopened findings detected.")
        rules.append(result)
        (failures if result["status"] == "FAIL" else []).append(result)

    if policy.get("fail_on_scanner_failure", False):
        failed = sum(item.get("failed", 0) + item.get("unavailable", 0) for item in scanner_items or [])
        result = _rule("fail_on_scanner_failure", "FAIL" if failed else "PASS", failed, 0, f"{failed} scanner failure/unavailable records." if failed else "No scanner failures or unavailable records.")
        rules.append(result)
        (failures if result["status"] == "FAIL" else []).append(result)

    required_scanners = set(policy.get("required_scanners", []) or [])
    if required_scanners:
        observed = {item.get("scanner") for item in scanner_items or []}
        missing = sorted(required_scanners - observed)
        result = _rule("required_scanners", "FAIL" if missing else "PASS", missing, sorted(required_scanners), f"Required scanners missing: {', '.join(missing)}." if missing else "All required scanners have execution records.")
        rules.append(result)
        (failures if result["status"] == "FAIL" else []).append(result)

    if failures:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    elif any(rule["status"] == "UNKNOWN" for rule in rules):
        status = "UNKNOWN"
    else:
        status = "PASS"
    unknown_reasons = [rule["reason"] for rule in rules if rule["status"] == "UNKNOWN" and rule.get("reason")]
    return {"status": status, "rules": rules, "failed_rules": failures, "warning_rules": warnings, "reason": "No configured policy rules were violated." if status == "PASS" else "; ".join(rule["reason"] for rule in (failures or warnings) if rule.get("reason")) or "; ".join(unknown_reasons) or "Policy could not be fully evaluated."}
