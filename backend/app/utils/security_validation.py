"""
Security and input validation utilities for AegisScan.
Provides robust protection against SSRF, DNS rebinding, cloud metadata abuse,
Path Traversal, and invalid target configurations.
"""

import ipaddress
import os
import re
import socket
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
from loguru import logger

# Allowed schemes for web targets
ALLOWED_URL_SCHEMES = {"http", "https"}

# Dangerous schemes that must be strictly rejected
DANGEROUS_SCHEMES = {
    "file", "gopher", "dict", "ftp", "ftps", "sftp", "tftp",
    "ldap", "ldaps", "data", "javascript", "vbscript", "jar"
}

# Known Cloud Metadata hostnames and IP addresses to always block
CLOUD_METADATA_HOSTS = {
    "instance-data",
    "metadata.google.internal",
    "metadata.goog",
    "169.254.169.254",
    "169.254.170.2",
    "100.100.100.200",
}

CLOUD_METADATA_NETWORKS = [
    ipaddress.ip_network("169.254.169.254/32"),
    ipaddress.ip_network("169.254.170.2/32"),
    ipaddress.ip_network("100.100.100.200/32"),
    ipaddress.ip_network("fd00:ec2::254/128"),
]


def is_ip_address(host: str) -> bool:
    """Check if host string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def is_safe_ip(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address, allow_private: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Check whether an IP address is safe for outbound security scanning.
    Blocks cloud metadata addresses, loopback, private ranges, link-local,
    multicast, and reserved ranges unless allow_private is explicitly enabled.
    """
    # 1. Always block cloud metadata endpoints
    for meta_net in CLOUD_METADATA_NETWORKS:
        if ip_obj in meta_net:
            return False, f"Destination IP {ip_obj} is a reserved cloud metadata endpoint."

    # 2. Check if private / loopback / link-local / reserved
    is_restricted = (
        ip_obj.is_loopback or
        ip_obj.is_private or
        ip_obj.is_link_local or
        ip_obj.is_multicast or
        ip_obj.is_reserved or
        ip_obj.is_unspecified
    )

    if is_restricted:
        if allow_private:
            return True, None
        return False, f"Destination IP {ip_obj} is a private, loopback, or internal address. Internal targets are disabled in public mode."

    return True, None


def resolve_and_validate_host(host: str, allow_private: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Resolve host via DNS and validate all resolved IP addresses against SSRF policies.
    """
    host_clean = host.split(":")[0].strip().lower()

    if host_clean in CLOUD_METADATA_HOSTS:
        return False, f"Access to cloud metadata host '{host_clean}' is prohibited."

    # Check if host is direct IP
    if is_ip_address(host_clean):
        ip_obj = ipaddress.ip_address(host_clean)
        return is_safe_ip(ip_obj, allow_private=allow_private)

    # Resolve hostname to IPs
    try:
        addr_info = socket.getaddrinfo(host_clean, None)
        if not addr_info:
            return False, f"Unable to resolve host '{host_clean}'."

        resolved_ips = set()
        for item in addr_info:
            sockaddr = item[4]
            ip_str = sockaddr[0]
            resolved_ips.add(ip_str)

        for ip_str in resolved_ips:
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                is_safe, error = is_safe_ip(ip_obj, allow_private=allow_private)
                if not is_safe:
                    return False, f"Host '{host_clean}' resolves to restricted IP {ip_str}: {error}"
            except ValueError:
                return False, f"Invalid resolved IP '{ip_str}' for host '{host_clean}'."

        return True, None
    except socket.gaierror as e:
        logger.debug(f"DNS resolution failure for host '{host_clean}': {e}")
        # Allow DNS resolution error to pass here only if in development mode; in strict mode reject
        if not allow_private:
            return False, f"Could not resolve host '{host_clean}' via DNS."
        return True, None
    except Exception as e:
        return False, f"Host validation error for '{host_clean}': {str(e)}"


def validate_url(url: Optional[str], allow_private: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate target URL format, scheme, and destination safety.
    Returns (is_valid, error_message).
    """
    if not url:
        return True, None

    url_str = url.strip()
    if len(url_str) > 500:
        return False, "URL length exceeds maximum allowed limit (500 characters)"

    try:
        parsed = urlparse(url_str)
        if not parsed.scheme:
            return False, "URL must include scheme (e.g., http:// or https://)"

        scheme_lower = parsed.scheme.lower()
        if scheme_lower in DANGEROUS_SCHEMES:
            return False, f"URL scheme '{scheme_lower}' is forbidden for security scans."

        if scheme_lower not in ALLOWED_URL_SCHEMES:
            return False, f"URL scheme '{scheme_lower}' is not allowed. Use http:// or https://"

        if not parsed.netloc:
            return False, "URL must include a valid host/domain name or IP address"

        # Check hostname
        host = parsed.netloc.split("@")[-1]  # Remove userinfo if present
        is_safe, host_err = resolve_and_validate_host(host, allow_private=allow_private)
        if not is_safe:
            return False, host_err

        return True, None
    except Exception as e:
        return False, f"Malformed URL: {str(e)}"


def validate_and_sanitize_path(path: Optional[str], allowed_root: Optional[Path] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Sanitize and check filesystem paths to prevent directory traversal exploits.
    Returns (is_valid, sanitized_path, error_message).
    """
    if not path:
        return True, None, None

    path_str = path.strip()
    if len(path_str) > 500:
        return False, None, "Path length exceeds maximum allowed limit (500 characters)"

    # Detect null byte injection
    if "\x00" in path_str:
        return False, None, "Path contains invalid null byte character"

    try:
        resolved_path = Path(path_str).expanduser().resolve()
        
        if allowed_root:
            root_resolved = Path(allowed_root).expanduser().resolve()
            if root_resolved != resolved_path and root_resolved not in resolved_path.parents:
                return False, None, f"Path '{path_str}' is outside the authorized root directory."

        return True, str(resolved_path), None
    except Exception as e:
        return False, None, f"Invalid filesystem path: {str(e)}"
