"""
URL normalization, deduplication, and fingerprinting service for Attack Surface discovery.
"""

import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Optional, Tuple, Dict, Any, List
from loguru import logger
from sqlalchemy.orm import Session

from app.models.attack_surface import AttackSurfaceItem, AttackSurfaceType, AttackSurfaceStatus


def normalize_url(raw_url: Optional[str]) -> Optional[str]:
    """
    Standardize a URL to prevent duplicate variants:
    - Lowercase scheme and host
    - Remove default ports (80 for http, 443 for https)
    - Remove fragment / anchor
    - Normalize path slashes (strip redundant slashes, trailing slash normalization)
    - Sort query parameters alphabetically while preserving values
    """
    if not raw_url:
        return None

    try:
        url_str = raw_url.strip()
        parsed = urlparse(url_str)
        if not parsed.scheme or not parsed.netloc:
            return url_str

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]

        # Path normalization: normalize redundant slashes
        path = parsed.path
        if not path:
            path = "/"
        else:
            # Replace duplicate slashes
            while "//" in path:
                path = path.replace("//", "/")
            # Remove trailing slash if length > 1 (e.g., '/login/' -> '/login')
            if len(path) > 1 and path.endswith("/"):
                path = path[:-1]

        # Query parameter normalization: sort keys
        query = ""
        if parsed.query:
            query_params = parse_qsl(parsed.query, keep_blank_values=True)
            # Sort by key then value for deterministic representation
            query_params.sort(key=lambda x: (x[0], x[1]))
            query = urlencode(query_params)

        # Reconstruct normalized URL (fragment omitted)
        normalized = urlunparse((scheme, netloc, path, "", query, ""))
        return normalized
    except Exception as e:
        logger.debug(f"URL normalization fallback for '{raw_url}': {e}")
        return raw_url.strip()


def generate_asset_fingerprint(
    asset_type: AttackSurfaceType,
    url: Optional[str],
    method: Optional[str] = "GET",
    path: Optional[str] = None,
    parameter: Optional[str] = None
) -> str:
    """
    Generate a deterministic fingerprint key for attack surface items.
    """
    norm_url = normalize_url(url) or ""
    norm_method = (method or "GET").upper().strip()
    norm_path = (path or "").strip()
    norm_param = (parameter or "").strip()
    norm_type = asset_type.value if isinstance(asset_type, AttackSurfaceType) else str(asset_type)

    raw_signature = f"{norm_type}|{norm_method}|{norm_url}|{norm_path}|{norm_param}"
    return hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()[:32]


def save_or_merge_attack_surface_item(
    db: Session,
    assessment_id: int,
    asset_type: AttackSurfaceType,
    name: Optional[str],
    url: Optional[str],
    method: Optional[str] = "GET",
    path: Optional[str] = None,
    parameter: Optional[str] = None,
    source: str = "crawler",
    risk_relevance: str = "medium",
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[AttackSurfaceItem, bool]:
    """
    Deduplicate and persist or update an attack surface item in the database.
    Returns (item, is_new_created).
    """
    norm_url = normalize_url(url)
    fingerprint = generate_asset_fingerprint(
        asset_type=asset_type,
        url=norm_url,
        method=method,
        path=path,
        parameter=parameter
    )

    # Check if this item exists for this assessment
    existing_item = (
        db.query(AttackSurfaceItem)
        .filter(
            AttackSurfaceItem.assessment_id == assessment_id,
            AttackSurfaceItem.fingerprint == fingerprint
        )
        .first()
    )

    if existing_item:
        # Merge discovery source provenance
        sources = list(existing_item.discovered_by or [])
        if source not in sources:
            sources.append(source)
            existing_item.discovered_by = sources

        # Merge metadata
        if metadata:
            current_meta = dict(existing_item.item_metadata or {})
            current_meta.update(metadata)
            existing_item.item_metadata = current_meta

        db.commit()
        db.refresh(existing_item)
        logger.debug(f"ASSET_DEDUPLICATED: id={existing_item.id} type='{existing_item.type.value}' url='{existing_item.url}'")
        return existing_item, False

    # Create new attack surface item
    new_item = AttackSurfaceItem(
        assessment_id=assessment_id,
        fingerprint=fingerprint,
        type=asset_type,
        name=name or path or norm_url,
        url=norm_url,
        method=(method or "GET").upper(),
        path=path,
        parameter=parameter,
        source=source,
        discovered_by=[source],
        status=AttackSurfaceStatus.ACTIVE,
        risk_relevance=risk_relevance,
        item_metadata=metadata or {}
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    logger.info(f"ASSET_DISCOVERED: id={new_item.id} type='{new_item.type.value}' url='{new_item.url}' source='{source}'")
    return new_item, True
