"""
Discovery orchestrator that coordinates all discovery modules.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from loguru import logger

from app.discovery.base import DiscoveryResult, DiscoveredAsset, AssetType
from app.discovery.crawler import WebCrawler
from app.discovery.endpoints import EndpointDiscovery
from app.discovery.technologies import TechnologyDetector


class DiscoveryOrchestrator:
    """
    Orchestrates the attack surface discovery process.
    Runs multiple discovery modules and aggregates results.
    """

    def __init__(
        self,
        enable_crawler: bool = True,
        enable_endpoint_discovery: bool = True,
        enable_technology_detection: bool = True,
        timeout: int = 60,
        max_pages: int = 50
    ):
        self.enable_crawler = enable_crawler
        self.enable_endpoint_discovery = enable_endpoint_discovery
        self.enable_technology_detection = enable_technology_detection
        self.timeout = timeout
        self.max_pages = max_pages

        # Discovery modules
        self.crawler = WebCrawler(max_pages=max_pages) if enable_crawler else None
        self.endpoint_discovery = EndpointDiscovery() if enable_endpoint_discovery else None
        self.tech_detector = TechnologyDetector() if enable_technology_detection else None

    async def discover(self, target_url: str) -> Dict[str, Any]:
        """
        Run all discovery modules and aggregate results.

        Args:
            target_url: The target URL to discover

        Returns:
            Aggregated discovery results
        """
        start_time = time.time()
        logger.info(f"Starting discovery for target: {target_url}")

        results = {
            "target_url": target_url,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "duration_ms": 0,
            "modules": {},
            "assets": [],
            "technologies": [],
            "errors": [],
            "stats": {
                "total_assets": 0,
                "by_type": {},
                "by_source": {},
                "high_risk_count": 0
            }
        }

        try:
            # Run discovery modules in parallel
            tasks = []

            if self.crawler:
                tasks.append(("crawler", self.crawler.discover(target_url)))

            if self.endpoint_discovery:
                tasks.append(("endpoints", self.endpoint_discovery.discover(target_url)))

            if self.tech_detector:
                tasks.append(("technologies", self.tech_detector.discover(target_url)))

            # Execute all tasks
            task_names = [t[0] for t in tasks]
            task_coros = [t[1] for t in tasks]

            task_results = await asyncio.gather(*task_coros, return_exceptions=True)

            # Process results
            all_assets: List[DiscoveredAsset] = []
            all_technologies: List[Dict[str, Any]] = []

            for name, result in zip(task_names, task_results):
                if isinstance(result, Exception):
                    error_msg = f"{name} discovery failed: {str(result)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["modules"][name] = {"status": "failed", "error": str(result)}
                else:
                    results["modules"][name] = {
                        "status": "completed",
                        "duration_ms": result.duration_ms,
                        "assets_found": len(result.assets)
                    }
                    all_assets.extend(result.assets)
                    all_technologies.extend(result.technologies)
                    results["errors"].extend(result.errors)
                    logger.info(f"{name} discovery completed: {len(result.assets)} assets found")

            # Deduplicate assets
            unique_assets = self._deduplicate_assets(all_assets)

            # Calculate stats
            by_type = {}
            by_source = {}
            high_risk_count = 0

            for asset in unique_assets:
                # By type
                type_key = asset.type.value if isinstance(asset.type, AssetType) else str(asset.type)
                by_type[type_key] = by_type.get(type_key, 0) + 1

                # By source
                by_source[asset.source or "unknown"] = by_source.get(asset.source or "unknown", 0) + 1

                # Risk count
                if asset.risk_relevance == "high":
                    high_risk_count += 1

            results["assets"] = [a.to_dict() for a in unique_assets]
            results["technologies"] = self._deduplicate_technologies(all_technologies)
            results["stats"] = {
                "total_assets": len(unique_assets),
                "by_type": by_type,
                "by_source": by_source,
                "high_risk_count": high_risk_count
            }

        except Exception as e:
            error_msg = f"Discovery orchestration failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        # Finalize
        results["duration_ms"] = int((time.time() - start_time) * 1000)
        results["completed_at"] = datetime.utcnow().isoformat()

        logger.info(f"Discovery completed: {results['stats']['total_assets']} assets found in {results['duration_ms']}ms")

        return results

    def _deduplicate_assets(self, assets: List[DiscoveredAsset]) -> List[DiscoveredAsset]:
        """Remove duplicate assets based on URL and path."""
        seen = set()
        unique = []

        for asset in assets:
            # Create a key for deduplication
            key = (asset.url or "", asset.path or "", asset.type.value if isinstance(asset.type, AssetType) else str(asset.type))

            if key not in seen:
                seen.add(key)
                unique.append(asset)

        return unique

    def _deduplicate_technologies(self, technologies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate technologies, keeping highest confidence."""
        by_name = {}

        for tech in technologies:
            name = tech.get("name", "")
            if name:
                if name not in by_name or tech.get("confidence", 0) > by_name[name].get("confidence", 0):
                    by_name[name] = tech

        return list(by_name.values())


async def run_discovery(target_url: str, db, assessment_id: int) -> Dict[str, Any]:
    """
    Run discovery and store results in database.

    Args:
        target_url: Target URL to discover
        db: Database session
        assessment_id: Assessment ID to associate assets with

    Returns:
        Discovery results
    """
    from app.models.asset import Asset
    from app.models.assessment import Assessment

    # Check assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    # Run discovery
    orchestrator = DiscoveryOrchestrator()
    results = await orchestrator.discover(target_url)

    # Store assets in database
    for asset_data in results.get("assets", []):
        db_asset = Asset(
            assessment_id=assessment_id,
            type=asset_data["type"],
            url=asset_data.get("url"),
            path=asset_data.get("path"),
            method=asset_data.get("method"),
            name=asset_data.get("name"),
            source=asset_data.get("source"),
            risk_relevance=asset_data.get("risk_relevance", "medium"),
            metadata_=asset_data.get("metadata")
        )
        db.add(db_asset)

    db.commit()

    return results
