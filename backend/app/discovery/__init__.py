"""
Attack Surface Discovery engine and utilities package.
"""

from app.discovery.engine import DiscoveryEngine, SafeBasicDiscoveryEngine
from app.discovery.normalizer import (
    normalize_url,
    generate_asset_fingerprint,
    save_or_merge_attack_surface_item
)

__all__ = [
    "DiscoveryEngine",
    "SafeBasicDiscoveryEngine",
    "normalize_url",
    "generate_asset_fingerprint",
    "save_or_merge_attack_surface_item",
]
