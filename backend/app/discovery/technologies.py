"""
Technology detection module.
Identifies frameworks, libraries, and technologies used by the target.
"""

import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from app.discovery.base import BaseDiscovery, DiscoveryResult, DiscoveredAsset, AssetType


class TechnologyDetector(BaseDiscovery):
    """
    Detects technologies used by a web application.
    Uses HTTP headers, HTML content, JavaScript files, and cookies.
    """

    # Technology signatures
    SIGNATURES = {
        # Frontend Frameworks
        "react": {
            "patterns": [r"react\.min\.js", r"react\.production\.min\.js", r"__REACT_DEVTOOLS_GLOBAL_HOOK__", r"data-reactroot"],
            "category": "Frontend Framework",
            "risk": "low"
        },
        "vue": {
            "patterns": [r"vue\.min\.js", r"vue\.runtime\.min\.js", r"__VUE__", r"data-v-"],
            "category": "Frontend Framework",
            "risk": "low"
        },
        "angular": {
            "patterns": [r"angular\.min\.js", r"ng-version", r"ng-app", r"angular\.module"],
            "category": "Frontend Framework",
            "risk": "low"
        },
        "next.js": {
            "patterns": [r"_next/static", r"__NEXT_DATA__", r"next/dist"],
            "category": "Frontend Framework",
            "risk": "low"
        },
        "svelte": {
            "patterns": [r"svelte", r"__svelte_component"],
            "category": "Frontend Framework",
            "risk": "low"
        },

        # Backend Frameworks
        "django": {
            "patterns": [r"csrftoken", r"django", r"__admin__"],
            "headers": ["x-frame-options"],
            "cookies": ["csrftoken", "sessionid"],
            "category": "Backend Framework",
            "risk": "low"
        },
        "flask": {
            "patterns": [r"flask"],
            "category": "Backend Framework",
            "risk": "low"
        },
        "express": {
            "patterns": [r"express", r"x-powered-by.*express"],
            "headers": ["x-powered-by"],
            "category": "Backend Framework",
            "risk": "low"
        },
        "fastapi": {
            "patterns": [r"fastapi", r"/docs", r"/openapi.json"],
            "category": "Backend Framework",
            "risk": "low"
        },
        "asp.net": {
            "patterns": [r"__VIEWSTATE", r"asp\.net", r"\.aspx"],
            "headers": ["x-aspnet-version"],
            "cookies": ["ASP.NET_SessionId"],
            "category": "Backend Framework",
            "risk": "low"
        },
        "php": {
            "patterns": [r"\.php", r"PHPSESSID"],
            "headers": ["x-powered-by"],
            "cookies": ["PHPSESSID"],
            "category": "Backend Framework",
            "risk": "low"
        },
        "laravel": {
            "patterns": [r"laravel", r"XSRF-TOKEN"],
            "cookies": ["laravel_session", "XSRF-TOKEN"],
            "category": "Backend Framework",
            "risk": "low"
        },
        "rails": {
            "patterns": [r"ruby", r"rails"],
            "cookies": ["_session"],
            "category": "Backend Framework",
            "risk": "low"
        },

        # UI Libraries
        "bootstrap": {
            "patterns": [r"bootstrap\.min\.css", r"bootstrap\.min\.js", r"class=.*container"],
            "category": "UI Library",
            "risk": "low"
        },
        "tailwindcss": {
            "patterns": [r"tailwind\.min\.css", r"class=.*flex.*items-center", r"tw-"],
            "category": "UI Library",
            "risk": "low"
        },
        "jquery": {
            "patterns": [r"jquery\.min\.js", r"\$\(", r"jQuery"],
            "category": "JavaScript Library",
            "risk": "low"
        },

        # State Management
        "redux": {
            "patterns": [r"redux\.min\.js", r"__REDUX_DEVTOOLS_EXTENSION__"],
            "category": "State Management",
            "risk": "low"
        },

        # Build Tools
        "webpack": {
            "patterns": [r"webpack", r"/static/js/main\.[a-f0-9]+\.js", r"__webpack_require__"],
            "category": "Build Tool",
            "risk": "low"
        },
        "vite": {
            "patterns": [r"vite", r"/src/.*\.jsx?", r"type=\"module\""],
            "category": "Build Tool",
            "risk": "low"
        },

        # CMS
        "wordpress": {
            "patterns": [r"wp-content", r"wp-includes", r"wordpress"],
            "category": "CMS",
            "risk": "low"
        },
        "drupal": {
            "patterns": [r"drupal", r"/sites/default/files"],
            "category": "CMS",
            "risk": "low"
        },

        # Cloud/CDN
        "cloudflare": {
            "headers": ["cf-ray", "cf-cache-status"],
            "category": "CDN",
            "risk": "low"
        },
        "aws": {
            "patterns": [r"amazonaws\.com", r"aws"],
            "headers": ["x-amz-cf-id"],
            "category": "Cloud",
            "risk": "low"
        },

        # Security Headers/Tools
        "nginx": {
            "headers": ["server"],
            "header_patterns": {"server": [r"nginx"]},
            "category": "Web Server",
            "risk": "low"
        },
        "apache": {
            "headers": ["server"],
            "header_patterns": {"server": [r"apache", r"httpd"]},
            "category": "Web Server",
            "risk": "low"
        },

        # Analytics & Tracking
        "google-analytics": {
            "patterns": [r"google-analytics\.com", r"gtag\(", r"ga\("],
            "category": "Analytics",
            "risk": "medium"
        },
        "google-tag-manager": {
            "patterns": [r"googletagmanager\.com", r"GTM-"],
            "category": "Analytics",
            "risk": "medium"
        },

        # Authentication
        "auth0": {
            "patterns": [r"auth0", r"auth0\.com"],
            "category": "Authentication",
            "risk": "medium"
        },
        "firebase": {
            "patterns": [r"firebase", r"firebaseapp\.com", r"firebaseio\.com"],
            "category": "Backend Service",
            "risk": "medium"
        },

        # API Documentation
        "swagger": {
            "patterns": [r"swagger-ui", r"/swagger", r"swagger\.js"],
            "category": "API Documentation",
            "risk": "medium"
        },
        "openapi": {
            "patterns": [r"/openapi\.json", r"/openapi\.yaml", r"openapi"],
            "category": "API Documentation",
            "risk": "medium"
        },

        # Monitoring
        "sentry": {
            "patterns": [r"sentry\.io", r"Sentry\.init", r"browser\.sentry-cdn\.com"],
            "category": "Monitoring",
            "risk": "medium"
        },
        "datadog": {
            "patterns": [r"datadoghq\.com", r"DD_RUM"],
            "category": "Monitoring",
            "risk": "medium"
        },

        # Dangerous/Debug
        "debug-endpoints": {
            "patterns": [r"/debug", r"/_debug", r"/trace", r"/actuator"],
            "category": "Debug/Info",
            "risk": "high"
        },
        "source-maps": {
            "patterns": [r"\.map\"|\.map'|sourceMappingURL"],
            "category": "Debug/Info",
            "risk": "medium"
        },
    }

    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
        self.detected: Dict[str, Dict[str, Any]] = {}

    async def discover(self, target_url: str, context: Optional[Dict[str, Any]] = None) -> DiscoveryResult:
        """
        Detect technologies used by the target application.

        Args:
            target_url: The base URL to analyze
            context: Optional context with pre-fetched data

        Returns:
            DiscoveryResult with detected technologies
        """
        import httpx
        import time

        result = DiscoveryResult()
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # Fetch the main page
                response = await client.get(target_url)

                # Analyze headers
                self._analyze_headers(dict(response.headers), result)

                # Analyze cookies
                self._analyze_cookies(response.cookies, result)

                # Analyze HTML content
                content = response.text
                self._analyze_content(content, result)

                # Extract and check JavaScript files
                js_files = self._extract_js_files(content, target_url)
                for js_url in js_files[:10]:  # Limit to first 10 JS files
                    try:
                        js_response = await client.get(js_url)
                        if js_response.status_code == 200:
                            self._analyze_js_content(js_response.text, js_url, result)
                    except Exception:
                        pass

        except Exception as e:
            result.add_error(f"Technology detection failed: {str(e)}")

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    def _analyze_headers(self, headers: Dict[str, str], result: DiscoveryResult):
        """Analyze HTTP headers for technology signatures."""
        headers_lower = {k.lower(): v for k, v in headers.items()}

        for tech_name, signature in self.SIGNATURES.items():
            # Check required headers
            if "headers" in signature:
                for header in signature["headers"]:
                    header_lower = header.lower()
                    if header_lower in headers_lower:
                        result.add_technology(
                            tech_name,
                            confidence=0.8
                        )
                        result.add_asset(DiscoveredAsset(
                            type=AssetType.HEADER,
                            name=header,
                            source="technology_detection",
                            risk_relevance=signature.get("risk", "low"),
                            metadata={"value": headers_lower[header_lower][:100]}  # Truncate
                        ))

            # Check header patterns
            if "header_patterns" in signature:
                for header, patterns in signature["header_patterns"].items():
                    header_lower = header.lower()
                    if header_lower in headers_lower:
                        header_value = headers_lower[header_lower]
                        for pattern in patterns:
                            if re.search(pattern, header_value, re.IGNORECASE):
                                result.add_technology(
                                    tech_name,
                                    confidence=0.9
                                )

    def _analyze_cookies(self, cookies, result: DiscoveryResult):
        """Analyze cookies for technology signatures."""
        for cookie_name in cookies.keys():
            result.add_asset(DiscoveredAsset(
                type=AssetType.COOKIE,
                name=cookie_name,
                source="technology_detection",
                risk_relevance="low",
                metadata={"secure": cookies.get(cookie_name, {}).get("secure", False)}
            ))

            # Check against signatures
            for tech_name, signature in self.SIGNATURES.items():
                if "cookies" in signature:
                    for pattern in signature["cookies"]:
                        if pattern.lower() in cookie_name.lower():
                            result.add_technology(
                                tech_name,
                                confidence=0.7
                            )

    def _analyze_content(self, content: str, result: DiscoveryResult):
        """Analyze HTML content for technology signatures."""
        for tech_name, signature in self.SIGNATURES.items():
            if "patterns" in signature:
                for pattern in signature["patterns"]:
                    if re.search(pattern, content, re.IGNORECASE):
                        result.add_technology(
                            tech_name,
                            confidence=0.7
                        )

    def _analyze_js_content(self, content: str, url: str, result: DiscoveryResult):
        """Analyze JavaScript file content."""
        for tech_name, signature in self.SIGNATURES.items():
            if "patterns" in signature:
                for pattern in signature["patterns"]:
                    if re.search(pattern, content, re.IGNORECASE):
                        result.add_technology(
                            tech_name,
                            confidence=0.6
                        )

    def _extract_js_files(self, content: str, base_url: str) -> List[str]:
        """Extract JavaScript file URLs from HTML content."""
        from urllib.parse import urljoin

        # Pattern to find script src attributes
        pattern = r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']'
        matches = re.findall(pattern, content, re.IGNORECASE)

        js_urls = []
        for match in matches:
            full_url = urljoin(base_url, match)
            if self._is_valid_url(full_url):
                js_urls.append(full_url)

        return list(set(js_urls))  # Deduplicate
