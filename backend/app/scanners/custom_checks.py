"""
AegisScan Native Custom Security Checks Engine.
Performs safe, non-destructive heuristic security assessments of headers, cookies, CORS, and configuration.
"""

import httpx
from typing import Dict, Any, List, Optional
from loguru import logger


def check_security_headers(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Evaluate response headers without making a network request."""
    normalized = {key.lower(): value for key, value in headers.items()}
    findings = []

    if not normalized.get("content-security-policy"):
        findings.append({"check_id": "MISSING_CSP", "status": "detected", "severity": "medium"})
    if normalized.get("x-content-type-options", "").lower() != "nosniff":
        findings.append({"check_id": "MISSING_X_CONTENT_TYPE_OPTIONS", "status": "detected", "severity": "low"})
    if not normalized.get("x-frame-options") and "frame-ancestors" not in normalized.get("content-security-policy", "").lower():
        findings.append({"check_id": "MISSING_CLICKJACKING_PROTECTION", "status": "detected", "severity": "medium"})
    if not normalized.get("referrer-policy"):
        findings.append({"check_id": "MISSING_REFERRER_POLICY", "status": "detected", "severity": "low"})
    if normalized.get("server") or normalized.get("x-powered-by"):
        findings.append({"check_id": "SERVER_BANNER_EXPOSED", "status": "potential", "severity": "low"})
    return findings


def check_cookie_security(set_cookie_headers: List[str]) -> List[Dict[str, Any]]:
    """Evaluate cookie attributes from raw Set-Cookie header values."""
    findings = []
    for cookie in set_cookie_headers:
        if not cookie:
            continue
        cookie_name = cookie.split("=", 1)[0].strip()
        lowered = cookie.lower()
        if "httponly" not in lowered:
            findings.append({"check_id": "COOKIE_MISSING_HTTPONLY", "cookie": cookie_name, "status": "detected", "severity": "medium"})
        if "secure" not in lowered:
            findings.append({"check_id": "COOKIE_MISSING_SECURE", "cookie": cookie_name, "status": "potential", "severity": "medium"})
        if "samesite" not in lowered:
            findings.append({"check_id": "COOKIE_MISSING_SAMESITE", "cookie": cookie_name, "status": "detected", "severity": "low"})
    return findings


def check_cors_policy(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Evaluate CORS response headers for unsafe wildcard credentials."""
    normalized = {key.lower(): value for key, value in headers.items()}
    if normalized.get("access-control-allow-origin") == "*" and normalized.get("access-control-allow-credentials", "").lower() == "true":
        return [{"check_id": "INSECURE_CORS_WILDCARD_WITH_CREDS", "status": "potential", "severity": "high"}]
    return []


async def execute_custom_security_checks(target_url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Run built-in safe heuristic checks against target URL.
    Returns structured raw results preserving evidence for Phase 5 normalization.
    """
    logger.info(f"CUSTOM_CHECKS_STARTED: target='{target_url}'")
    checks_results: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False, follow_redirects=True) as client:
            resp = await client.get(target_url)
            headers = {k.lower(): v for k, v in resp.headers.items()}

            # 1. Check Content-Security-Policy (CSP)
            csp = headers.get("content-security-policy")
            if not csp:
                checks_results.append({
                    "check_id": "SEC-HDR-001",
                    "name": "Missing Content-Security-Policy (CSP)",
                    "category": "security_headers",
                    "status": "detected",
                    "severity": "medium",
                    "evidence": "Header 'Content-Security-Policy' was not returned by server.",
                    "details": "CSP restricts resource loading and mitigates cross-site scripting (XSS) attacks."
                })
            else:
                checks_results.append({
                    "check_id": "SEC-HDR-001",
                    "name": "Content-Security-Policy (CSP) Present",
                    "category": "security_headers",
                    "status": "not_applicable",
                    "severity": "info",
                    "evidence": f"CSP: {csp[:100]}..."
                })

            # 2. Check X-Content-Type-Options
            xcto = headers.get("x-content-type-options")
            if not xcto or xcto.lower() != "nosniff":
                checks_results.append({
                    "check_id": "SEC-HDR-002",
                    "name": "Missing X-Content-Type-Options: nosniff",
                    "category": "security_headers",
                    "status": "detected",
                    "severity": "low",
                    "evidence": f"Header value: '{xcto}' (expected 'nosniff')",
                    "details": "Prevents MIME-sniffing vulnerabilities."
                })

            # 3. Check X-Frame-Options / Clickjacking Protection
            xfo = headers.get("x-frame-options")
            if not xfo and not csp:
                checks_results.append({
                    "check_id": "SEC-HDR-003",
                    "name": "Missing Clickjacking Protection (X-Frame-Options / frame-ancestors)",
                    "category": "security_headers",
                    "status": "detected",
                    "severity": "medium",
                    "evidence": "Neither 'X-Frame-Options' nor CSP 'frame-ancestors' was configured.",
                    "details": "Allows application to be embedded in iframes on malicious third-party origins."
                })

            # 4. Check Referrer-Policy
            rp = headers.get("referrer-policy")
            if not rp:
                checks_results.append({
                    "check_id": "SEC-HDR-004",
                    "name": "Missing Referrer-Policy Header",
                    "category": "security_headers",
                    "status": "detected",
                    "severity": "low",
                    "evidence": "Header 'Referrer-Policy' was not present.",
                    "details": "Sensitive paths or tokens in query parameters may leak via Referer header."
                })

            # 5. Check Strict-Transport-Security (HSTS) if HTTPS
            if target_url.lower().startswith("https://"):
                hsts = headers.get("strict-transport-security")
                if not hsts:
                    checks_results.append({
                        "check_id": "SEC-HDR-005",
                        "name": "Missing Strict-Transport-Security (HSTS)",
                        "category": "tls_configuration",
                        "status": "detected",
                        "severity": "medium",
                        "evidence": "HTTPS connection lacks HSTS header.",
                        "details": "HSTS enforces secure HTTPS-only connections."
                    })

            # 6. Check Cookie Security Flags (HttpOnly, Secure, SameSite)
            set_cookie_headers = resp.headers.get_list("set-cookie") if hasattr(resp.headers, "get_list") else [headers.get("set-cookie")]
            for raw_cookie in set_cookie_headers:
                if not raw_cookie:
                    continue
                cookie_lower = raw_cookie.lower()
                c_name = raw_cookie.split("=")[0].strip()

                if "httponly" not in cookie_lower:
                    checks_results.append({
                        "check_id": "SEC-CK-001",
                        "name": f"Cookie '{c_name}' Missing HttpOnly Flag",
                        "category": "cookie_security",
                        "status": "detected",
                        "severity": "medium",
                        "evidence": f"Set-Cookie: {raw_cookie}",
                        "details": "HttpOnly flag protects session tokens from client-side script theft."
                    })

                if "samesite" not in cookie_lower:
                    checks_results.append({
                        "check_id": "SEC-CK-002",
                        "name": f"Cookie '{c_name}' Missing SameSite Attribute",
                        "category": "cookie_security",
                        "status": "detected",
                        "severity": "low",
                        "evidence": f"Set-Cookie: {raw_cookie}",
                        "details": "SameSite prevents cross-site request forgery (CSRF)."
                    })

            # 7. Check Insecure CORS wildcard configuration
            cors_acao = headers.get("access-control-allow-origin")
            cors_acac = headers.get("access-control-allow-credentials")
            if cors_acao == "*":
                checks_results.append({
                    "check_id": "SEC-CORS-001",
                    "name": "Permissive Wildcard Access-Control-Allow-Origin (*)",
                    "category": "cors_configuration",
                    "status": "potential",
                    "severity": "low",
                    "evidence": "Access-Control-Allow-Origin: *",
                    "details": "Permits arbitrary origins to read API response data."
                })

    except Exception as e:
        logger.warning(f"Custom security checks network error for '{target_url}': {e}")
        checks_results.append({
            "check_id": "SEC-ERR-001",
            "name": "Target Connectivity Check",
            "category": "network",
            "status": "error",
            "severity": "info",
            "evidence": str(e)
        })

    detected_count = sum(1 for c in checks_results if c.get("status") in ["detected", "potential"])
    logger.info(f"CUSTOM_CHECKS_COMPLETED: target='{target_url}' total_checks={len(checks_results)} issues_detected={detected_count}")

    return {
        "scanner": "custom_checks",
        "target": target_url,
        "total_checks_run": len(checks_results),
        "issues_detected": detected_count,
        "results": checks_results
    }
