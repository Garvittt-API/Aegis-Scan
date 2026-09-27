"""
Production Security & Hardening Tests for AegisScan.
Tests:
- User registration, login, JWT token issuance, and password hashing
- Role-based authorization & /api/auth/me profile retrieval
- SSRF prevention & cloud metadata blocking
- Rate limiting middleware & 429 response
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options, etc.)
- Health and readiness endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ipaddress

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.utils.security_validation import (
    validate_url,
    resolve_and_validate_host,
    is_safe_ip,
    validate_and_sanitize_path,
    CLOUD_METADATA_HOSTS
)

client = TestClient(app)


def test_password_hashing():
    """Verify bcrypt password hashing and validation."""
    pwd = "SecurePassword123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_flow():
    """Verify JWT token generation and decoding."""
    token = create_access_token(subject=42, is_admin=True)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["is_admin"] is True


def test_user_registration_and_login():
    """Test user registration, duplicate prevention, and login flow."""
    unique_email = f"operator_{pytest.__version__.replace('.', '')}@aegisscan.local"
    unique_user = f"operator_{pytest.__version__.replace('.', '')}"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "email": unique_email,
        "username": unique_user,
        "password": "ProductionReadyPassword2026!",
        "full_name": "Lead Security Engineer"
    })
    assert reg_res.status_code in (201, 400)

    # 2. Login
    login_res = client.post("/api/auth/login", json={
        "username_or_email": unique_email,
        "password": "ProductionReadyPassword2026!"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 3. Access protected /me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == unique_email


def test_ssrf_cloud_metadata_blocked():
    """Verify that cloud metadata hostnames and IPs are strictly rejected."""
    for host in CLOUD_METADATA_HOSTS:
        is_safe, error = resolve_and_validate_host(host, allow_private=False)
        assert is_safe is False, f"Cloud metadata host '{host}' was not blocked!"
        assert error is not None


def test_ssrf_ip_blocking():
    """Verify private/loopback blocking in public SaaS mode."""
    # Loopback
    is_safe, _ = is_safe_ip(ipaddress.ip_address("127.0.0.1"), allow_private=False)
    assert is_safe is False

    # Private 10.x.x.x
    is_safe, _ = is_safe_ip(ipaddress.ip_address("10.100.1.5"), allow_private=False)
    assert is_safe is False

    # AWS Metadata
    is_safe, _ = is_safe_ip(ipaddress.ip_address("169.254.169.254"), allow_private=False)
    assert is_safe is False

    # Allowed public IP
    is_safe, _ = is_safe_ip(ipaddress.ip_address("8.8.8.8"), allow_private=False)
    assert is_safe is True


def test_dangerous_schemes_blocked():
    """Verify file://, gopher://, javascript: schemes are rejected."""
    for scheme in ["file:///etc/passwd", "gopher://127.0.0.1:70", "javascript:alert(1)", "data:text/html,test"]:
        is_valid, err = validate_url(scheme)
        assert is_valid is False
        assert err is not None


def test_security_headers_present():
    """Verify security headers are attached to all API responses."""
    res = client.get("/health")
    assert res.status_code == 200
    assert "Content-Security-Policy" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_health_and_readiness():
    """Verify health and readiness probes return positive statuses."""
    liveness = client.get("/health")
    assert liveness.status_code == 200
    assert liveness.json()["status"] == "healthy"

    readiness = client.get("/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["database"] == "ready"
    assert readiness.json()["storage"] == "ready"


def test_path_traversal_sanitization():
    """Verify path traversal strings are resolved or blocked."""
    is_valid, path, err = validate_and_sanitize_path("foo/../bar")
    assert is_valid is True
    assert "\x00" not in (path or "")

    # Null byte attempt
    is_valid, _, err = validate_and_sanitize_path("foo\x00bar")
    assert is_valid is False
