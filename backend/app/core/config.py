"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "AegisScan"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./aegisscan.db"

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://127.0.0.1:5173"])

    # Scanners - paths to external tools
    zap_path: Optional[str] = None
    nuclei_path: Optional[str] = None
    semgrep_path: Optional[str] = None
    dependency_check_path: Optional[str] = None

    # Optional Ollama for AI features
    ollama_url: Optional[str] = None

    # Reports
    reports_dir: Path = Path("./reports")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
