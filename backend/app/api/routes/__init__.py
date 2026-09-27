"""
API routes package.
"""

from app.api.routes import (
    health,
    auth,
    targets,
    assessments,
    attack_surface,
    discovery,
    scan_jobs,
    findings,
    assets,
    reports,
    analytics
)

__all__ = [
    "health",
    "auth",
    "targets",
    "assessments",
    "attack_surface",
    "discovery",
    "scan_jobs",
    "findings",
    "assets",
    "reports",
    "analytics",
]
