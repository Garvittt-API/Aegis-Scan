"""
Production Security Middleware for AegisScan.
Includes:
- Security Headers enforcement (CSP, X-Frame-Options, HSTS, etc.)
- Sliding-window IP-based API Rate Limiter
- Safe Global Exception and Error Response handling
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies strict, modern HTTP security headers to all outgoing responses.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 1. Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:* ws://localhost:* http://127.0.0.1:* ws://127.0.0.1:* https:;"
        )

        # 2. Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 3. Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # 4. Strict Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 5. Restrict dangerous browser features
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"

        # 6. HSTS (Strict-Transport-Security) for HTTPS / Production
        if settings.environment.lower() == "production" or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window in-memory rate limiter per client IP address.
    Protects API endpoints against brute-force and resource-exhaustion attacks.
    """

    def __init__(self, app):
        super().__init__(app)
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.auth_requests: Dict[str, List[float]] = defaultdict(list)

    def _clean_old_requests(self, timestamps: List[float], window_seconds: float = 60.0) -> List[float]:
        now = time.time()
        cutoff = now - window_seconds
        return [ts for ts in timestamps if ts > cutoff]

    async def dispatch(self, request: Request, call_next):
        # Extract client IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        path = request.url.path

        # Stricter limit on sensitive auth routes
        if path.startswith("/api/auth/login") or path.startswith("/api/auth/register"):
            recent = self._clean_old_requests(self.auth_requests[client_ip])
            if len(recent) >= settings.auth_rate_limit_per_minute:
                logger.warning(f"RATE_LIMIT_EXCEEDED (Auth): ip='{client_ip}' path='{path}'")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Too Many Requests",
                        "detail": f"Authentication rate limit exceeded ({settings.auth_rate_limit_per_minute} req/min). Please wait before retrying."
                    },
                    headers={"Retry-After": "60"}
                )
            recent.append(now)
            self.auth_requests[client_ip] = recent
        else:
            # General API rate limit
            recent = self._clean_old_requests(self.requests[client_ip])
            if len(recent) >= settings.rate_limit_per_minute:
                logger.warning(f"RATE_LIMIT_EXCEEDED: ip='{client_ip}' path='{path}'")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Too Many Requests",
                        "detail": f"API request rate limit exceeded ({settings.rate_limit_per_minute} req/min). Please slow down."
                    },
                    headers={"Retry-After": "60"}
                )
            recent.append(now)
            self.requests[client_ip] = recent

        return await call_next(request)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Sanitize unhandled 500 exceptions in production so that internal server details,
    database schemas, or stack traces are not leaked to external callers.
    """
    logger.error(f"UNHANDLED_EXCEPTION at {request.method} {request.url.path}: {exc}")
    
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "path": request.url.path
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected server error occurred. Please contact the system administrator.",
                "status_code": 500
            }
        )
