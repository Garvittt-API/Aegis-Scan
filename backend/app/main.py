"""
AegisScan Backend - Main FastAPI Application
Production-hardened API with Security Headers, Rate Limiting, and Authentication.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import (
    SecurityHeadersMiddleware,
    RateLimiterMiddleware,
    global_exception_handler
)
from app.api.routes import (
    health,
    auth,
    targets,
    assessments,
    findings,
    assets,
    attack_surface,
    discovery,
    scan_jobs,
    reports,
    analytics
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Private targets allowed: {settings.allow_private_targets}")

    # Initialize database
    init_db()
    logger.info("Database initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down AegisScan...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    AegisScan - Automated Application Security Assessment & Verification Platform

    A multi-engine security assessment platform that combines DAST, SAST, dependency analysis,
    attack-surface discovery and custom security checks into one evidence-driven workflow.
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 1. Add Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. Add Rate Limiting Middleware
app.add_middleware(RateLimiterMiddleware)

# 3. Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 4. Register global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# 5. Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(targets.router, prefix="/api/targets", tags=["Targets"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])
app.include_router(discovery.router, prefix="/api", tags=["Discovery"])
app.include_router(attack_surface.router, prefix="/api", tags=["Attack Surface"])
app.include_router(scan_jobs.router, prefix="/api", tags=["Scan Jobs & Orchestrator"])
app.include_router(findings.router, prefix="/api/findings", tags=["Findings"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

# Keep database initialized for lightweight CLI and testing clients
init_db()


@app.get("/")
async def root():
    """Root endpoint redirecting to API documentation."""
    return {
        "message": "Welcome to AegisScan API",
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/api/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
