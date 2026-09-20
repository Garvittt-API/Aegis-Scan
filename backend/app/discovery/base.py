"""
Base classes for discovery modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class AssetType(str, Enum):
    """Type of discovered asset."""
    PAGE = "page"
    ENDPOINT = "endpoint"
    API_ENDPOINT = "api_endpoint"
    JAVASCRIPT_FILE = "javascript_file"
    CSS_FILE = "css_file"
    IMAGE = "image"
    FORM = "form"
    PARAMETER = "parameter"
    COOKIE = "cookie"
    HEADER = "header"
    EXTERNAL_DOMAIN = "external_domain"
    TECHNOLOGY = "technology"
    CONFIG_FILE = "config_file"
    SOURCE_MAP = "source_map"


@dataclass
class DiscoveredAsset:
    """Represents a discovered asset in the attack surface."""
    type: AssetType
    url: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    name: Optional[str] = None
    source: Optional[str] = None  # How it was discovered
    risk_relevance: str = "medium"  # low, medium, high
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "url": self.url,
            "path": self.path,
            "method": self.method,
            "name": self.name,
            "source": self.source,
            "risk_relevance": self.risk_relevance,
            "metadata": self.metadata
        }


class DiscoveryResult:
    """Result of a discovery operation."""

    def __init__(self):
        self.assets: List[DiscoveredAsset] = []
        self.technologies: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.duration_ms: int = 0

    def add_asset(self, asset: DiscoveredAsset):
        """Add a discovered asset."""
        self.assets.append(asset)

    def add_technology(self, name: str, version: Optional[str] = None, confidence: float = 0.5):
        """Add a detected technology."""
        self.technologies.append({
            "name": name,
            "version": version,
            "confidence": confidence
        })

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "assets": [a.to_dict() for a in self.assets],
            "technologies": self.technologies,
            "errors": self.errors,
            "duration_ms": self.duration_ms,    
            "stats": {
                "total_assets": len(self.assets),
                "by_type": self._count_by_type()
            }
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count assets by type."""
        counts = {}
        for asset in self.assets:
            key = asset.type.value
            counts[key] = counts.get(key, 0) + 1
        return counts


class BaseDiscovery(ABC):
    """Base class for discovery modules."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    @abstractmethod
    async def discover(self, target_url: str, context: Optional[Dict[str, Any]] = None) -> DiscoveryResult:
        """
        Perform discovery on the target.

        Args:
            target_url: The base URL to discover
            context: Optional context (e.g., existing assets, credentials)

        Returns:
            DiscoveryResult with discovered assets
        """
        pass

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        return url.startswith(('http://', 'https://'))

    def _is_same_origin(self, base_url: str, target_url: str) -> bool:
        """Check if two URLs have the same origin."""
        from urllib.parse import urlparse
        base = urlparse(base_url)
        target = urlparse(target_url)
        return base.scheme == target.scheme and base.netloc == target.netloc
