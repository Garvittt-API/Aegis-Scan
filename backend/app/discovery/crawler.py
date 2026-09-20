"""
Web crawler for discovering pages, endpoints, and assets.
"""

import re
from typing import Dict, Any, Optional, List, Set
from urllib.parse import urljoin, urlparse, parse_qs
import time

from app.discovery.base import BaseDiscovery, DiscoveryResult, DiscoveredAsset, AssetType


class WebCrawler(BaseDiscovery):
    """
    Web crawler that discovers pages, endpoints, forms, and static assets.
    Uses simple HTTP requests and HTML parsing.
    """

    def __init__(
        self,
        timeout: int = 30,
        max_depth: int = 2,
        max_pages: int = 50,
        follow_redirects: bool = True
    ):
        super().__init__(timeout)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.follow_redirects = follow_redirects

        # Tracking
        self.visited: Set[str] = set()
        self.to_visit: List[tuple] = []  # (url, depth)
        self.found_urls: Set[str] = set()

    async def discover(self, target_url: str, context: Optional[Dict[str, Any]] = None) -> DiscoveryResult:
        """
        Crawl the target application to discover assets.

        Args:
            target_url: The base URL to crawl
            context: Optional context with credentials, cookies, etc.

        Returns:
            DiscoveryResult with discovered assets
        """
        import httpx

        result = DiscoveryResult()
        start_time = time.time()

        # Normalize target URL
        target_url = target_url.rstrip('/')
        parsed_target = urlparse(target_url)

        # Initialize crawl queue
        self.to_visit = [(target_url, 0)]
        self.visited = set()

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=self.follow_redirects,
                verify=False  # For testing purposes
            ) as client:
                while self.to_visit and len(self.visited) < self.max_pages:
                    url, depth = self.to_visit.pop(0)

                    if url in self.visited:
                        continue

                    self.visited.add(url)

                    try:
                        # Fetch page
                        response = await client.get(url)

                        # Add page asset
                        result.add_asset(DiscoveredAsset(
                            type=AssetType.PAGE,
                            url=url,
                            path=urlparse(url).path or "/",
                            source="crawler",
                            risk_relevance=self._assess_risk_relevance(url, response),
                            metadata={
                                "status_code": response.status_code,
                                "content_type": response.headers.get("content-type", ""),
                                "content_length": len(response.content)
                            }
                        ))

                        # Only parse HTML content
                        if "text/html" in response.headers.get("content-type", ""):
                            content = response.text

                            # Extract links
                            if depth < self.max_depth:
                                links = self._extract_links(content, url)
                                for link in links:
                                    if link not in self.visited:
                                        self.to_visit.append((link, depth + 1))

                            # Extract forms
                            forms = self._extract_forms(content, url)
                            for form in forms:
                                result.add_asset(form)

                            # Extract static assets
                            assets = self._extract_static_assets(content, url)
                            for asset in assets:
                                result.add_asset(asset)

                            # Extract API endpoints from JavaScript
                            api_endpoints = self._extract_api_endpoints_from_js(content, url)
                            for endpoint in api_endpoints:
                                result.add_asset(endpoint)

                    except Exception as e:
                        result.add_error(f"Error crawling {url}: {str(e)}")

        except Exception as e:
            result.add_error(f"Crawl failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    def _extract_links(self, content: str, base_url: str) -> List[str]:
        """Extract links from HTML content."""
        links = []

        # Pattern for href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        src_pattern = r'src=["\']([^"\']+)["\']'

        for pattern in [href_pattern, src_pattern]:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Skip fragments, javascript, and mailto links
                if match.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:')):
                    continue

                # Convert to absolute URL
                full_url = urljoin(base_url, match)

                # Only include same-origin URLs
                if self._is_same_origin(base_url, full_url):
                    # Remove fragment
                    full_url = full_url.split('#')[0]
                    if full_url and full_url not in self.visited:
                        links.append(full_url)

        return list(set(links))

    def _extract_forms(self, content: str, base_url: str) -> List[DiscoveredAsset]:
        """Extract forms from HTML content."""
        forms = []

        # Simple form extraction (can be improved with proper HTML parser)
        form_pattern = r'<form[^>]*>(.*?)</form>'
        form_matches = re.findall(form_pattern, content, re.IGNORECASE | re.DOTALL)

        for i, form_content in enumerate(form_matches):
            # Extract action
            action_match = re.search(r'action=["\']([^"\']*)["\']', form_content, re.IGNORECASE)
            action = action_match.group(1) if action_match else ""

            # Extract method
            method_match = re.search(r'method=["\']([^"\']*)["\']', form_content, re.IGNORECASE)
            method = method_match.group(1).upper() if method_match else "GET"

            # Build full URL
            full_url = urljoin(base_url, action) if action else base_url

            # Extract input fields
            input_pattern = r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>'
            inputs = re.findall(input_pattern, form_content, re.IGNORECASE)

            forms.append(DiscoveredAsset(
                type=AssetType.FORM,
                url=full_url,
                path=urlparse(full_url).path,
                method=method,
                name=f"Form {i+1}",
                source="crawler",
                risk_relevance="high" if method == "POST" else "medium",
                metadata={
                    "action": action,
                    "method": method,
                    "inputs": inputs
                }
            ))

        return forms

    def _extract_static_assets(self, content: str, base_url: str) -> List[DiscoveredAsset]:
        """Extract static assets (JS, CSS, images) from HTML content."""
        assets = []

        # JavaScript files
        js_pattern = r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']'
        for match in re.findall(js_pattern, content, re.IGNORECASE):
            full_url = urljoin(base_url, match)
            assets.append(DiscoveredAsset(
                type=AssetType.JAVASCRIPT_FILE,
                url=full_url,
                path=urlparse(full_url).path,
                name=match.split('/')[-1],
                source="crawler",
                risk_relevance="medium",  # JS files can contain sensitive info
            ))

        # CSS files
        css_pattern = r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']'
        for match in re.findall(css_pattern, content, re.IGNORECASE):
            full_url = urljoin(base_url, match)
            assets.append(DiscoveredAsset(
                type=AssetType.CSS_FILE,
                url=full_url,
                path=urlparse(full_url).path,
                name=match.split('/')[-1],
                source="crawler",
                risk_relevance="low",
            ))

        # Images (less important but still useful for mapping)
        img_pattern = r'<img[^>]+src=["\']([^"\']+\.(jpg|jpeg|png|gif|svg|webp)[^"\']*)["\']'
        for match, _ in re.findall(img_pattern, content, re.IGNORECASE):
            full_url = urljoin(base_url, match)
            assets.append(DiscoveredAsset(
                type=AssetType.IMAGE,
                url=full_url,
                path=urlparse(full_url).path,
                name=match.split('/')[-1],
                source="crawler",
                risk_relevance="low",
            ))

        return assets

    def _extract_api_endpoints_from_js(self, content: str, base_url: str) -> List[DiscoveredAsset]:
        """Extract potential API endpoints from JavaScript code."""
        endpoints = []

        # Patterns for API endpoints
        api_patterns = [
            r'["\'](/api/[^"\']+)["\']',
            r'["\'](/v\d+/[^"\']+)["\']',
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.[a-z]+\(["\']([^"\']+)["\']',
            r'\$\.ajax\({[^}]*url:\s*["\']([^"\']+)["\']',
            r'\.get\(["\']([^"\']+)["\']\)',
            r'\.post\(["\']([^"\']+)["\']\)',
        ]

        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Skip if it looks like a file path or variable
                if match.startswith('/') or match.startswith('http'):
                    full_url = urljoin(base_url, match)
                    endpoints.append(DiscoveredAsset(
                        type=AssetType.API_ENDPOINT,
                        url=full_url,
                        path=urlparse(full_url).path,
                        source="js_analysis",
                        risk_relevance="high",
                        metadata={"discovered_in": "javascript"}
                    ))

        return endpoints

    def _assess_risk_relevance(self, url: str, response) -> str:
        """Assess risk relevance of a URL."""
        url_lower = url.lower()

        # High risk indicators
        high_risk_patterns = [
            '/admin', '/api', '/login', '/logout', '/register',
            '/password', '/reset', '/upload', '/config', '/settings',
            '/dashboard', '/panel', '/debug', '/test', '/dev'
        ]

        for pattern in high_risk_patterns:
            if pattern in url_lower:
                return "high"

        # Check for sensitive status codes
        if response.status_code in [401, 403]:
            return "high"
        if response.status_code in [500, 502, 503]:
            return "medium"

        # Check for sensitive content types
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return "medium"

        return "low"
