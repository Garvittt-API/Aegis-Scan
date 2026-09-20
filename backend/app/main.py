"""
AegisScan Backend - Main FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import health, targets, assessments, findings, assets, attack_surface, discovery, scan_jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")


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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(targets.router, prefix="/api/targets", tags=["Targets"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])
app.include_router(discovery.router, prefix="/api", tags=["Discovery"])
app.include_router(attack_surface.router, prefix="/api", tags=["Attack Surface"])
app.include_router(scan_jobs.router, prefix="/api", tags=["Scan Jobs & Orchestrator"])
app.include_router(findings.router, prefix="/api/findings", tags=["Findings"])
app.include_router(assets.router, prefix="/api", tags=["Assets"])

# Keep the local-first SQLite database usable for API clients that do not run
# the ASGI lifespan context (including lightweight CLI and test clients).
init_db()


@app.get("/")
async def root():
    """Root endpoint redirecting to API docs."""
    return {
        "message": "Welcome to AegisScan API",
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
