"""
Endpoint discovery module.
Discovers and analyzes API endpoints, routes, and parameters.
"""

import re
from typing import Dict, Any, Optional, List, Set
from urllib.parse import urlparse, parse_qs, urljoin
import time

from app.discovery.base import BaseDiscovery, DiscoveryResult, DiscoveredAsset, AssetType


class EndpointDiscovery(BaseDiscovery):
    """
    Discovers API endpoints and analyzes their parameters.
    Combines multiple discovery techniques.
    """

    # Common API patterns to check
    COMMON_API_PATHS = [
        "/api",
        "/api/v1",
        "/api/v2",
        "/graphql",
        "/rest",
        "/swagger",
        "/swagger-ui",
        "/api-docs",
        "/docs",
        "/openapi.json",
        "/openapi.yaml",
        "/health",
        "/status",
        "/metrics",
        "/actuator",
        "/actuator/health",
        "/actuator/metrics",
        "/debug",
        "/trace",
        "/.env",
        "/config.json",
        "/package.json",
        "/composer.json",
        "/robots.txt",
        "/sitemap.xml",
        "/.git/config",
        "/.svn/entries",
        "/backup",
        "/backup.sql",
        "/dump",
        "/admin",
        "/admin/login",
        "/api/users",
        "/api/auth",
        "/api/login",
        "/api/register",
        "/api/config",
        "/ws",
        "/socket.io",
    ]

    # HTTP methods to test (non-destructive)
    HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]

    def __init__(
        self,
        timeout: int = 30,
        check_common_paths: bool = True,
        extract_parameters: bool = True
    ):
        super().__init__(timeout)
        self.check_common_paths = check_common_paths
        self.extract_parameters = extract_parameters

    async def discover(self, target_url: str, context: Optional[Dict[str, Any]] = None) -> DiscoveryResult:
        """
        Discover endpoints and API paths.

        Args:
            target_url: The base URL to analyze
            context: Optional context with existing discoveries

        Returns:
            DiscoveryResult with discovered endpoints
        """
        import httpx

        result = DiscoveryResult()
        start_time = time.time()

        target_url = target_url.rstrip('/')

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=False
            ) as client:
                # Check common paths
                if self.check_common_paths:
                    await self._check_common_paths(client, target_url, result)

                # Check robots.txt for additional paths
                await self._analyze_robots_txt(client, target_url, result)

                # Check for OpenAPI/Swagger documentation
                await self._check_api_documentation(client, target_url, result)

        except Exception as e:
            result.add_error(f"Endpoint discovery failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    async def _check_common_paths(
        self,
        client,
        base_url: str,
        result: DiscoveryResult
    ):
        """Check for common API paths and sensitive endpoints."""
        for path in self.COMMON_API_PATHS:
            url = f"{base_url}{path}"
            try:
                # Use HEAD first (lighter weight)
                response = await client.head(url)

                # If HEAD fails, try GET
                if response.status_code == 405:
                    response = await client.get(url)

                if response.status_code < 400:
                    # Endpoint exists
                    risk = self._assess_endpoint_risk(path, response.status_code)

                    result.add_asset(DiscoveredAsset(
                        type=AssetType.API_ENDPOINT if "/api" in path else AssetType.ENDPOINT,
                        url=url,
                        path=path,
                        method="GET",
                        name=path,
                        source="common_paths_check",
                        risk_relevance=risk,
                        metadata={
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type", ""),
                            "content_length": response.headers.get("content-length", "0")
                        }
                    ))

                    # Try to extract parameters from response
                    if self.extract_parameters and "application/json" in response.headers.get("content-type", ""):
                        await self._extract_parameters_from_response(response, result)

            except Exception:
                pass  # Endpoint doesn't exist or is not accessible

    async def _analyze_robots_txt(
        self,
        client,
        base_url: str,
        result: DiscoveryResult
    ):
        """Parse robots.txt for additional paths."""
        robots_url = f"{base_url}/robots.txt"

        try:
            response = await client.get(robots_url)

            if response.status_code == 200:
                # Add robots.txt itself
                result.add_asset(DiscoveredAsset(
                    type=AssetType.CONFIG_FILE,
                    url=robots_url,
                    path="/robots.txt",
                    source="robots_txt_analysis",
                    risk_relevance="low"
                ))

                # Extract disallowed paths (these are interesting!)
                content = response.text
                disallow_pattern = r'Disallow:\s*(.+)'
                allow_pattern = r'Allow:\s*(.+)'

                for pattern in [disallow_pattern, allow_pattern]:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        path = match.strip()
                        if path and path != '/':
                            result.add_asset(DiscoveredAsset(
                                type=AssetType.ENDPOINT,
                                url=f"{base_url}{path}",
                                path=path,
                                source="robots_txt",
                                risk_relevance="high",  # Disallowed paths are often sensitive
                                metadata={"from_robots_txt": True}
                            ))

        except Exception:
            pass

    async def _check_api_documentation(
        self,
        client,
        base_url: str,
        result: DiscoveryResult
    ):
        """Check for OpenAPI/Swagger documentation."""
        doc_paths = [
            "/openapi.json",
            "/swagger.json",
            "/api-docs",
            "/docs/json",
            "/v1/docs",
            "/api/v1/docs"
        ]

        for path in doc_paths:
            url = f"{base_url}{path}"
            try:
                response = await client.get(url)

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")

                    if "json" in content_type:
                        result.add_asset(DiscoveredAsset(
                            type=AssetType.CONFIG_FILE,
                            url=url,
                            path=path,
                            name="OpenAPI/Swagger Documentation",
                            source="api_docs_discovery",
                            risk_relevance="medium",
                            metadata={"type": "openapi_spec"}
                        ))

                        # Parse OpenAPI spec for endpoints
                        try:
                            spec = response.json()
                            await self._parse_openapi_spec(spec, base_url, result)
                        except Exception:
                            pass

            except Exception:
                pass

    async def _parse_openapi_spec(
        self,
        spec: dict,
        base_url: str,
        result: DiscoveryResult
    ):
        """Parse OpenAPI specification for endpoints."""
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            for method in methods.keys():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    method_info = methods[method]

                    result.add_asset(DiscoveredAsset(
                        type=AssetType.API_ENDPOINT,
                        url=f"{base_url}{path}",
                        path=path,
                        method=method.upper(),
                        name=method_info.get("summary", path),
                        source="openapi_spec",
                        risk_relevance="medium",
                        metadata={
                            "description": method_info.get("description"),
                            "parameters": [p.get("name") for p in method_info.get("parameters", [])],
                            "from_spec": True
                        }
                    ))

    async def _extract_parameters_from_response(
        self,
        response,
        result: DiscoveryResult
    ):
        """Extract parameters from API response."""
        try:
            data = response.json()

            # Recursively extract keys
            def extract_keys(obj, prefix=""):
                keys = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        keys.append(full_key)
                        keys.extend(extract_keys(value, full_key))
                elif isinstance(obj, list) and obj:
                    keys.extend(extract_keys(obj[0], prefix))
                return keys

            keys = extract_keys(data)
            for key in keys[:20]:  # Limit to 20 parameters
                result.add_asset(DiscoveredAsset(
                    type=AssetType.PARAMETER,
                    name=key,
                    source="api_response_analysis",
                    risk_relevance="low"
                ))

        except Exception:
            pass

    def _assess_endpoint_risk(self, path: str, status_code: int) -> str:
        """Assess risk level of an endpoint."""
        path_lower = path.lower()

        # Critical paths
        critical_patterns = [
            '/.env', '/.git', '/config', '/backup', '/dump',
            '/debug', '/actuator', '/admin'
        ]
        for pattern in critical_patterns:
            if pattern in path_lower:
                return "high"

        # Sensitive paths
        sensitive_patterns = [
            '/api/auth', '/api/user', '/api/admin',
            '/login', '/password', '/api/key'
        ]
        for pattern in sensitive_patterns:
            if pattern in path_lower:
                return "high"

        # API endpoints
        if '/api' in path_lower:
            return "medium"

        return "low"
