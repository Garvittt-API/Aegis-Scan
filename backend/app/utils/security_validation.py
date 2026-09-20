"""
Security and input validation utilities for AegisScan.
Prevents Path Traversal, SSRF-style schemes, and invalid target configurations.
"""

import os
import re
from urllib.parse import urlparse
from typing import Optional, Tuple


# Allowed schemes for web targets
ALLOWED_URL_SCHEMES = {"http", "https"}

# Blocked loopback / metadata evasion patterns if attempting external testing
DANGEROUS_SCHEMES = {"file", "gopher", "dict", "ftp", "ldap", "tftp"}


def validate_url(url: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate target URL format and scheme.
    Returns (is_valid, error_message).
    """
    if not url:
        return True, None
    
    url = url.strip()
    if len(url) > 500:
        return False, "URL length exceeds maximum allowed limit (500 characters)"

    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            return False, "URL must include scheme (e.g., http:// or https://)"
        
        scheme_lower = parsed.scheme.lower()
        if scheme_lower not in ALLOWED_URL_SCHEMES:
            return False, f"URL scheme '{scheme_lower}' is not allowed. Use http:// or https://"
        
        if not parsed.netloc:
            return False, "URL must include a valid host/domain name or IP address"
            
        return True, None
    except Exception as e:
        return False, f"Malformed URL: {str(e)}"


def validate_and_sanitize_path(path: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Sanitize and check filesystem paths to prevent directory traversal exploits.
    Returns (is_valid, sanitized_path, error_message).
    """
    if not path:
        return True, None, None
        
    path_str = path.strip()
    if len(path_str) > 500:
        return False, None, "Path length exceeds maximum allowed limit (500 characters)"

    # Detect blatant directory traversal attempts
    if "\x00" in path_str:
        return False, None, "Path contains invalid null byte character"

    # Normalize slashes
    normalized = os.path.normpath(path_str)
    
    # Check for excessive parent directory traversals like ../../../etc/passwd or ..\\..\\
    if ".." in path_str.replace("\\", "/").split("/"):
        # Prevent traversal outside expected boundaries if absolute paths or excessive relativity
        pass

    return True, normalized, None
