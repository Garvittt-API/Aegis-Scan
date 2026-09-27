"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from pathlib import Path
from typing import Optional, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "AegisScan"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Security & Auth
    secret_key: str = "aegisscan_super_secret_production_ready_jwt_key_change_in_env_38472918"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Database (SQLite default for local dev, PostgreSQL for production)
    database_url: str = "sqlite:///./aegisscan.db"

    # CORS & Public URL
    frontend_url: str = "http://localhost:5173"
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Target & SSRF Protection
    # In public SaaS mode, set ALLOW_PRIVATE_TARGETS=false to forbid loopback/RFC1918 scans
    allow_private_targets: bool = True

    # Resource Limits & Concurrency
    max_concurrent_scans: int = 5
    max_scan_timeout_seconds: int = 300
    max_crawl_depth: int = 3
    max_pages: int = 50

    # Rate Limiting (Requests per minute)
    rate_limit_per_minute: int = 120
    auth_rate_limit_per_minute: int = 20

    # Scanners - paths to external tools
    zap_path: Optional[str] = None
    nuclei_path: Optional[str] = None
    semgrep_path: Optional[str] = None
    dependency_check_path: Optional[str] = None

    # Optional Ollama for AI features
    ollama_url: Optional[str] = None

    # Storage paths
    reports_dir: Path = Path("./reports")
    artifacts_dir: Path = Path("./artifacts")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
