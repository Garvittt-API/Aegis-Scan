"""
Security, password hashing, and JWT token management for AegisScan.
Implements robust PBKDF2-HMAC-SHA256 password hashing and signed JWT access tokens.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from loguru import logger

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# Bearer token extractor
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    """
    Secure password hashing using PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salt.
    Format: pbkdf2_sha256$100000$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(16)
    iterations = 100000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its stored hash using constant-time comparison.
    """
    try:
        if not hashed_password or not plain_password:
            return False

        if hashed_password.startswith("pbkdf2_sha256$"):
            parts = hashed_password.split("$")
            if len(parts) != 4:
                return False
            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected_hash = parts[3]
            derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(derived.hex(), expected_hash)
        else:
            # Fallback for legacy plain or simple hashes
            return hmac.compare_digest(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None, is_admin: bool = False) -> str:
    """Generate a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "is_admin": is_admin,
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode failed: {e}")
        return None


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Retrieve current user if a valid bearer token is provided, otherwise None.
    Allows backward-compatible open access for CLI and test runners.
    """
    token_val = None
    if auth_header and auth_header.credentials:
        token_val = auth_header.credentials
    elif token:
        token_val = token

    if not token_val:
        return None

    payload = decode_access_token(token_val)
    if not payload:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = int(user_id_str)
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        return user
    except Exception:
        return None


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Enforce authentication: retrieve active user or raise HTTP 401 Unauthorized.
    """
    user = await get_optional_current_user(token=token, auth_header=auth_header, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Enforce admin privileges or raise HTTP 403 Forbidden."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this operation."
        )
    return current_user
